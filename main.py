"""
Super simple voice assistant.
It publishes MQTT messages when commands are triggered. 
"""
import sys
import os
from time import sleep
import logging
import json
from collections import namedtuple
from vosk import Model, KaldiRecognizer
from pyaudio import PyAudio, paInt16
from jellyfish import jaro_winkler_similarity
import paho.mqtt.client as mqtt

MODEL = os.environ['VOSK_MODEL_PATH']

MQTT_SERVER = os.environ['MQTT_SERVER']
MQTT_PORT = int(os.environ.get('MQTT_PORT', '1883'))
MSG_ON_FAIL = os.environ.get('MQTT_ON_FAIL', 'False').lower() == 'true'
ASSISTANT_NAME = os.environ.get('ASSISTANT_NAME', 'Zhu Li')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(ASSISTANT_NAME)

def fetch_commands():
    """Parse the commands.json file

    This function parse the commands set in the commands.json file into a dictionary.

    The key is the command itself and values are stored in a namedtuple called `Action`.

    {
        'do the thing': Action(topic='light', score=0.72, payload=None),
        'bedroom': Action(topic='bedroom', score=0.72, payload=None),
    }

    Returns:
        (dict): A dictionary with all the voice commands to be triggered by the assistant.

    """
    Action = namedtuple('Action', 'topic score payload')
    with open('./commands.json', 'r') as file_:
        raw_commands = json.load(file_)

    commands = {key: Action(**value) for key, value in raw_commands.items()}

    return commands


def get_mic():
    """Get the microphone stream

    See the pyaudio library documentation for more info.
    https://people.csail.mit.edu/hubert/pyaudio/

    Return:
        The microphone object.
    """
    audio_devices = PyAudio()                 
    mic_stream = audio_devices.open(format=paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    mic_stream.start_stream()

    return mic_stream


def process_audio(recognizer, mic_stream):
    """
    Input chunks of the microphone stream into the speech model and output text.

    Args:
        recognizer: The KaldiRecognizer object from vosk.
        mic_stream: The microphone stream from get_mic().

    Returns:
        A string or None

    """
    audio_chunk = mic_stream.read(4096)
    if recognizer.AcceptWaveform(audio_chunk):
        text = json.loads(recognizer.Result())
        if text['text'] and text['text'] != 'huh':  # Filtering out 'huh' coming from noise.
            logger.info('Audio Process: %s' % text['text'])
            return (text['text'])
    
    return None


def find_pattern(text):
    """  
    Compare the input text with the commands in `commands` dictionary.
    It generates a score for each command.
    The score defines how similar the text is to the command. 
    See https://jamesturk.github.io/jellyfish/ for more info.

    The commands are then sorted by score. If the highest score is equal or above
    its score threshold it is selected and return as a Pattern namedtuple.
    Example: 
        Pattern(input='Zhu li do the thing', action='do the thing', score=1)

    If it does not find any match, it also returns a Pattern object, but the action is set to `None`
    and the score get a dictionary with a score for each available command.

    Args:
        text (str): string from process_audio()

    Return:
        (:obj:`namedtuple`): A Pattern namedtuple

    """
    Pattern = namedtuple('Pattern', 'input action score')
      
    analyze_store = {}
    for key in commands.keys():    
        string_match = ASSISTANT_NAME + ' ' + key
        similarity = jaro_winkler_similarity(text, string_match.lower())

        analyze_store[key] = (string_match, similarity)

    analyze_sorted = {key: value for key, value in sorted(
        analyze_store.items(), 
        key=lambda item: item[1][1], 
        reverse=True,
    )}

    msg = 'Similarity: '
    first_element = None
    for key, value in analyze_sorted.items():
        if not first_element:
            first_element = key
        msg += f'{value[0]}: {value[1]} '    
    logger.info(msg)    

    if analyze_sorted[first_element][1] >= commands[first_element].score:
        return Pattern(text, first_element, analyze_sorted[first_element][1])
    
    return Pattern(text, None, analyze_sorted)


def set_payload(pattern):
    """ Build payload

    This function is used to build the payload to be send with the MQTT message.
    It creates a dictionary with the `action`'s name, the `input` from the speech to text & the matching `score` it got.
    It also appends the payload set in the `commands.json` file.
    
    Args:
        pattern (:obj:`namedtuple`): A Pattern namedtuple.

    Return:
        (dict): Final payload in a dictionary.

    """
    payload = commands[pattern.action].payload
    payload_extra = {
        'action': f'{ASSISTANT_NAME} {pattern.action}',
        'input': pattern.input,
        'score': pattern.score
    }

    if payload is None:
        payload = payload_extra
    else:
        payload.update(payload_extra)

    return payload


def trigger_action(mqtt_client, pattern):
    """Send a MQTT message succeeding match

    Function used when a match is triggered.
    The mqtt topic is build with the assistant's name and the action's topic. e.g: `zhuli/light`.

    Attrs:
        mqtt_client: A mqtt connection object. 
        pattern (:obj:`namedtuple`): A Pattern namedtuple.

    """
        
    action = commands[pattern.action]
    logger.info('%s %s Triggered' % (ASSISTANT_NAME, pattern.action))
    mqtt_topic = ASSISTANT_NAME.lower().replace(' ', '') + '/' + action.topic

    payload = set_payload(pattern)

    mqtt_client.publish(mqtt_topic, payload=json.dumps(payload), qos=1)


def trigger_fail(mqtt_client, pattern):
    """Send a MQTT message on failing match

    Function used when a match fails.
    The mqtt topic is build with the assistant's name. e.g: `zhuli/fail`.
    With also dump all the commands' scores in it. 
    It can be useful if you want to keep some logs.

    Attrs:
        mqtt_client: A mqtt connection object.
        pattern (:obj:`namedtuple`): A Pattern namedtuple.

    """
    payload = {'input': pattern.input}
    payload.update({'scores': pattern.score})

    mqtt_failed_topic = ASSISTANT_NAME.lower().replace(' ', '') + '/' + 'fail'

    mqtt_client.publish(mqtt_failed_topic, payload=json.dumps(payload), qos=1)


def main():
    """Main loop.
    """
    mic_stream = get_mic()
    recognizer = KaldiRecognizer(Model(MODEL), 16000)

    mqtt_client = mqtt.Client(client_id='', clean_session=True, userdata=None, protocol=mqtt.MQTTv311, transport='tcp')
    mqtt_client.connect(MQTT_SERVER, port=MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()  # Needed to keep the mqtt connection alive.

    while True:
        try:
            text = process_audio(recognizer, mic_stream)
            if text:
                pattern = find_pattern(text)
                if pattern.action:
                    trigger_action(mqtt_client, pattern)
                else:
                    if MSG_ON_FAIL:
                        trigger_fail(mqtt_client, pattern)

        except KeyboardInterrupt:
            logger.warning('Terminating!')
            mic_stream.close()
            mqtt_client.loop_stop()
            sys.exit(0)
        except Exception as err:
            logger.exception(err)
            logger.warning('Restarting in:')
            for i in range(3, 0, -1):
                logger.warning(i)
                sleep(1)
            main()   


if __name__ == '__main__':
    commands = fetch_commands()
    main()
