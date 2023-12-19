import sys
from time import sleep
import logging
import json
from collections import namedtuple
from vosk import Model, KaldiRecognizer
from pyaudio import PyAudio, paInt16
from jellyfish import jaro_winkler_similarity
import paho.mqtt.client as mqtt

MODEL = './vosk-model-small-en-us-0.15'

MQTT_SERVER = '10.87.88.150'
MQTT_PORT = 1883

ASSISTANT_NAME = 'Zhu Li'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(ASSISTANT_NAME)

Action = namedtuple('Action', 'topic score playload')
Patern = namedtuple('Patern', 'input action score')

commands = {
    'energize': Action('energize', 0.72, None),
    'desk': Action('desk', 0.75, None),
    'do the thing': Action('light', 0.72, None),
    'romantica': Action('romantica', 0.72, None),
    'bedroom': Action('bedroom', 0.72, None),
}

def get_mic():
    audio_devices = PyAudio()                 
    mic_stream = audio_devices.open(format=paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)

    return mic_stream


def process_audio(recognizer, mic_stream):
    audio_chunk = mic_stream.read(4096)
    if recognizer.AcceptWaveform(audio_chunk):
        text = json.loads(recognizer.Result())
        if text['text'] and text['text'] != 'huh':
            logger.info('Audio Process: %s' % text['text'])
            return (text['text'])
    
    return None


def find_pattern(text):  
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
        return Patern(text, first_element, analyze_sorted[first_element][1])
    
    return None


def set_playload(patern):
    playload = commands[patern.action].playload
    playload_extra = {
        'action': f'{ASSISTANT_NAME} {patern.action}',
        'input': patern.input,
        'score': patern.score
    }

    if playload is None:
        playload = playload_extra
    else:
        playload.update(playload_extra)

    return playload


def trigger_action(mqtt_client, patern):
    action = commands[patern.action]
    logger.info('%s %s Triggered' % (ASSISTANT_NAME, patern.action))
    mqtt_topic = ASSISTANT_NAME.lower().replace(' ', '') + '/' + action.topic

    playload = set_playload(patern)

    mqtt_client.publish(mqtt_topic, payload=json.dumps(playload), qos=1)


def main():
    mic_stream = get_mic()
    mic_stream.start_stream()
    recognizer = KaldiRecognizer(Model(MODEL), 16000)

    mqtt_client = mqtt.Client(client_id='', clean_session=True, userdata=None, protocol=mqtt.MQTTv311, transport='tcp')
    mqtt_client.connect(MQTT_SERVER, port=MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()
    
    while True:
        try:
            text = process_audio(recognizer, mic_stream)
            if text:
                patern = find_pattern(text)

                if patern:
                    trigger_action(mqtt_client, patern)

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
    main()
