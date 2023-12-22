"""
Plugin for the Google speech recognition
"""
from pocketsphinx import Decoder
from speech.base import SpeechPlugin
from config import SAMPLE_RATE


class Sphinx(SpeechPlugin):

    def __init__(self):
        super().__init__()
        self.decoder = Decoder(samprate=SAMPLE_RATE)
    
    def microphone_input(self, stream):
        try:
            self.decoder.start_utt()
            self.decoder.process_raw(stream, full_utt=True)
        finally:
            self.decoder.end_utt()

    def output(self):
        hypothesis = self.decoder.hyp()
        self._logger.debug('Sphinx Score %f' % hypothesis.score)
        if hypothesis is not None:
            return hypothesis.hypstr
    