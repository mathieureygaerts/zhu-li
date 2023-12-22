"""
Plugin for the Vosk speech recognition toolkit.
"""
import json
from vosk import Model, KaldiRecognizer
from speech.base import SpeechPlugin
from config import VOSK_MODEL, SAMPLE_RATE


class Vosk(SpeechPlugin):

    def __init__(self):
        super().__init__()
        self._recognizer = KaldiRecognizer(Model(VOSK_MODEL), SAMPLE_RATE)
    
    def microphone_input(self, stream):
        self._recognizer.AcceptWaveform(stream)

    def output(self):
        text = json.loads(self._recognizer.Result())
        if text['text'] and text['text'] != 'huh':  # Filtering out 'huh' coming from noise.
            return (text['text'])
            
        return None