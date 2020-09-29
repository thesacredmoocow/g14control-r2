import os
import sys

import yaml


class Config:
    def __init__(self, G14dir, callback=None):
        self.callback = callback
        self.G14dir = G14dir
        self.config = None
        self.load_config()

    def get(self, key, default=None):
        return default if not self.config else self.config.get(key, default)

    def set(self, key, value):
        if self.config is None:
            self.config = {}
        self.config[key] = value
        self.update_config()

    def set_nested(self, parent, key, value):
        if self.config is None:
            self.config = {}
        if not self.config.get(parent):
            self.config[parent] = {}
        self.config[parent][key] = value
        self.update_config()

    def load_config(self):  # Small function to load the config and return it after parsing
        if getattr(sys, 'frozen', False):  # Sets the path accordingly whether it is a python script or a frozen .exe
            config_loc = os.path.join(self.G14dir, "config.yml")  # Set absolute path for config.yaml
        elif __file__:
            config_loc = os.path.join(self.G14dir, "data\config.yml")  # Set absolute path for config.yaml

        with open(config_loc, 'r') as config_file:
            self.config = yaml.load(config_file, Loader=yaml.FullLoader)
            return self.config



    def update_config(self):
        if getattr(sys, 'frozen', False):  # Sets the path accordingly whether it is a python script or a frozen .exe
            config_loc = os.path.join(self.G14dir, "config.yml")  # Set absolute path for config.yaml
        elif __file__:
            config_loc = os.path.join(self.G14dir, "data\config.yml")  # Set absolute path for config.yaml

        with open(config_loc, 'w') as config_file:
            yaml.dump(self.config, config_file, sort_keys=False)
        if self.callback:
            self.callback(self.config)


class UserSettings(Config):

    def get_settings_key(self, plugged_in=False, game_running=False):
        plugged_in_string = "plugged_in" if plugged_in else "unplugged"
        gaming_string = "_game_running" if game_running else ""
        return plugged_in_string + gaming_string

    def set(self, key, value, plugged_in=False, game_running=False):
        settings_key = self.get_settings_key(plugged_in, game_running)
        if self.config is None:
            self.config = {}
        if self.config.get(settings_key) is None:
            self.config[settings_key] = {}
        self.config[settings_key][key] = value
        self.update_config()

    def get(self, key, default=None, plugged_in=False, game_running=False):
        settings_key = self.get_settings_key(plugged_in, game_running)
        return default if not self.config.get(settings_key) else self.config[settings_key].get(key, default)

    def get_plan(self, plugged_in=False, game_running=False):
        settings_key = self.get_settings_key(plugged_in, game_running)
        return self.config.get(settings_key)

    def set_nested(self, parent, key, value, plugged_in=False, game_running=False):
        raise NotImplemented

    def load_config(self):  # Small function to load the config and return it after parsing
        if getattr(sys, 'frozen', False):  # Sets the path accordingly whether it is a python script or a frozen .exe
            config_loc = os.path.join(self.G14dir, "settings.yml")  # Set absolute path for config.yaml
        elif __file__:
            config_loc = os.path.join(self.G14dir, "data\settings.yml")  # Set absolute path for config.yaml
        try:
            with open(config_loc, 'r') as config_file:
                self.config = yaml.load(config_file, Loader=yaml.FullLoader)
        except:
            self.config = {}
        finally:
            return self.config

    def update_config(self):
        if getattr(sys, 'frozen', False):  # Sets the path accordingly whether it is a python script or a frozen .exe
            config_loc = os.path.join(self.G14dir, "settings.yml")  # Set absolute path for config.yaml
        elif __file__:
            config_loc = os.path.join(self.G14dir, "data\settings.yml")  # Set absolute path for config.yaml

        with open(config_loc, 'w+') as config_file:
            yaml.dump(self.config, config_file, sort_keys=False)
        if self.callback:
            self.callback(self.config)
