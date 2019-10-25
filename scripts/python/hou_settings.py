"""
    Simple JSON based settings manager

    Stores the json files under Dcos/houdinixx.x/tool_name.json

    Usage:

    import hou_settings

    settings = hou_settings.Settings("my_tool_name")
    settings.set("my_setting", "my_value")

    print settings.value("my_setting")

"""

import os
import json


class Settings(object):

    def __init__(self, toolname=None, filepath=None):

        self.filename = None
        if filepath:
            self.filename = filepath

        if toolname:
            self.filename = os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"), toolname + ".json")

        if not self.filename:
            self.filename = os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"), "user_settings.json")

        self._settings_dic = {}

        if os.path.exists(self.filename):
            self._load()

    def set(self, key, value):
        self._settings_dic[key] = value
        self._save()

    def value(self, key):
        if key in self._settings_dic:
            return self._settings_dic[key]
        else:
            return None

    def _load(self):
        with open(self.filename, 'r') as fp:
            try:
                self._settings_dic = json.load(fp)
            except:
                pass

    def _save(self):
        with open(self.filename, 'w') as fp:
            json.dump(self._settings_dic, fp)
