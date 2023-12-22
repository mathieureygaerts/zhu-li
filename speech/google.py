"""
Plugin for the Google speech recognition
"""

import os
import json
from vosk import Model, KaldiRecognizer
from speech.base import SpeechPlugin
from config import VOSK_MODEL


class Google(SpeechPlugin):

    def __init__(self):
        super().__init__()
        # TODO
    
    def microphone_input(self, stream):
        # TODO
        pass

    def output(self):
        # TODO
        return 'Hello World!'
    