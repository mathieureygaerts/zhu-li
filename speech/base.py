"""
Base plugin for the different speech recognition tools.
Speech Plugins should inherits from the this base class.
"""
from abc import ABC, abstractmethod
from lib.logger import logger

class speechPlugin(ABC):

    def __init__(self):
        self._logger = logger
    
    @abstractmethod
    def microphone_input():
        pass