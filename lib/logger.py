"""
Logger module
"""
import logging
import os

ASSISTANT_NAME = os.environ.get('ASSISTANT_NAME', 'Zhu Li')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(ASSISTANT_NAME)