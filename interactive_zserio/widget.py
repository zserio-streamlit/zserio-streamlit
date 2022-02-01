import streamlit as st

from interactive_zserio.logger import Logger

class Widget:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def _key(self, key):
        return self._name + "_" + key

    def _log(self, *args):
        Logger.log(self.name + ":", *args)
