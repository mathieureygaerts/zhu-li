# Zhu li

Zhu li is a super simple voice assistant. It publishes MQTT messages when commands are triggered.
Those messages can then be used by something like Home Assistant to toggle lights.

## Requirements

|Softwares|Notes|
|---|---|
|Python 3|Tested with 3.10. It would most probably also work with 3.9.|
|MQTT Broker|Tested with Mosquitto. You may already have an instance running if you use Zigbee2MQTT.|
|Some kind of home automatization system|Tested with Home Assistant.|


### Python requirements

All the needed requirements are set in the requirements.txt file. I would suggest to install them in a new python environment.
`pip install -r requirements.txt`

### Environment variables

Before running the script, you need to set a few environment variables: `VOSK_MODEL_PATH`, `MQTT_SERVER`.

By default, this script uses Vosk, a speech recognition toolkit. It supports multiple languages and have small models than can run on a raspberry pi.
Download the model you want from `https://alphacephei.com/vosk/`. 
I tested this with the `vosk-model-small-en-us-0.15` model.

If you placed the unzipped folder beside this script, the environment variable would look something like: `VOSK_MODEL_PATH=./vosk-model-small-en-us-0.15`


#### Variable list
|Name|Default|Description|
|---|---|---|
|`MQTT_SERVER`||Ip address of the MQTT broker|
|`MQTT_PORT`|`1883`|Port|
|`ASSISTANT_NAME`|`Zhu Li`|Name of the Assistant|
|`MSG_ON_FAIL`|`False`|Send a MQTT message with the `fail` topic (e.g: `zhuli/fail`) on failing match.|
|`SPEECH_TOOLKIT`|`vosk`|You can change the speech toolkit used by setting this variable.|
|`SAMPLE_RATE`|`16000`|Use to change the default sample rate.|
|`VOSK_MODEL_PATH`||Path to the Vosk Model|
|`LOGGER`|`info`|Can also be set to `debug`|


## Set the voice commands

You can set the voice commands by modifying the `commands.yml` file. A command is defined by a dictionary.

```json
{
    "do the thing": {
        "topic": "light",
        "score": 0.72,
        "payload": null
    }
}
```

The key defines the command. To activate it, you need to say the assistant's name first. e.g:
> Zhu Li do the thing.

The topic defines the name of the mqtt topic. It will always be prefixed by the assistant name first. e.g:
`zhuli/light`

The score defines how close the result of the voice command need to match the command to be triggered. 1 means it needs a perfect match, 0 means anything will trigger it.
Set it too low and it will trigger all the time, set it to high and it will rarely trigger. Tweak the score in function of your speech and model.

To help to determine a score that works for you, look at the logs when running the script. Say something and you will see the score it got for each commands. If the highest score is equal or above the score you set for that command, it will trigger.
```text
INFO:Zhu Li:Audio Process: julie do to thing
INFO:Zhu Li:Similarity: Zhu Li do the thing: 0.8239422084623323 Zhu Li diningroom: 0.6131907308377896 Zhu Li bedroom: 0.6129785247432307 Zhu Li kitchen: 0.6129785247432307 Zhu Li thank you: 0.6044117647058824 Zhu Li energize: 0.5986928104575163 Zhu Li livingroom: 0.592156862745098 Zhu Li desk: 0.5874713521772345 Zhu Li romantica: 0.5491557734204793 Zhu Li entrance: 0.5429738562091503 Zhu Li laundry: 0.4943977591036415 
INFO:Zhu Li:Zhu Li do the thing Triggered
```

The payload is there if you want to pass along extra data in the mqtt message. It should be a dictionary. 



## MQTT message format

The published topic will be the name of the assistant in lower case & without any space plus the topic value of the triggered command. e.g `zhuli/light`

The message will include a json payload with the command that got triggered, the input it got from the voice & the score.
```json
{
    "action": "Zhu li do the thing",
    "input": "julie do to thing",
    "score": 0.8239422084623323
}
```

If you also set a payload in the `commands.yml` for that action, it will be added here.


## Running

Once all the above requirements are fulfilled, simply run the main.py script.

You will need to set your home assistant to listen for the mqtt messages and trigger your devices accordingly.


## Add an alternative speech recognition toolkit.

Alternative toolkits can by added by creating a plugin file within the speech folder.
When the script starts, it fetches the `SPEECH_TOOLKIT` environment variable and look for a matching python file.
`SPEECH_TOOLKIT=sphinx` will look for `speech/sphinx.py`.

In your plugin, create a class that inherits from SpeechPlugin.
The name of the class needs to match the toolkit's name with the first letter capitalized.

Looks at the files in the speech folder to see how to write the needed methods.