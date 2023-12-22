"""
Store all the config shared by the code.
"""
import os
import logging

ASSISTANT_NAME = os.environ.get('ASSISTANT_NAME', 'Zhu Li')

# Logging
LOGGER = os.environ.get('LOGGER', 'info')
if LOGGER == 'info':
    log_level = logging.INFO
elif LOGGER == 'debug':
    log_level = logging.DEBUG
logging.basicConfig(level=log_level)
logger = logging.getLogger(ASSISTANT_NAME)

# MQTT configs
MQTT_SERVER = os.environ['MQTT_SERVER']
MQTT_PORT = int(os.environ.get('MQTT_PORT', '1883'))
MSG_ON_FAIL = os.environ.get('MQTT_ON_FAIL', 'False').lower() == 'true'

# Toolkit selections
SPEECH_TOOLKIT = os.environ.get('SPEECH_TOOLKIT', 'vosk')

# Vosk
VOSK_MODEL = os.environ['VOSK_MODEL_PATH']