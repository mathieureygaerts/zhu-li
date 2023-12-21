"""
Plugin for the Vosk speech recognition toolkit.
"""
import os
import json
from vosk import Model, KaldiRecognizer
from .base import speechPlugin

MODEL = os.environ['VOSK_MODEL_PATH']

class Vosk(speechPlugin):

    def __init__(self):
        super().__init__()
        self._recognizer = KaldiRecognizer(Model(MODEL), 16000)
    
    def microphone_input(self, stream):
        self._recognizer.AcceptWaveform(stream)

    def output(self):
        text = json.loads(self._recognizer.Result())
        if text['text'] and text['text'] != 'huh':  # Filtering out 'huh' coming from noise.
            return (text['text'])
            
        return None