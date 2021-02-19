from typing import Optional
from pathlib import Path
from os.path import join, isfile

import configparser
import os

class ConfigFileReader:
    def __init__(self, name, defaultValue = None, section = 'DEFAULT'):
        self.name = name
        self.defaultValue = defaultValue
        self.section = section

    def __call__(self) -> Optional[str]:
        if self.config_has_section:
            return self.config[self.section].get(self.name, self.defaultValue)
        return self.defaultValue

    @property
    def config(self):
        config = configparser.ConfigParser()
        if self.config_path is not None:
            config.read(self.config_path)
        return config

    @property
    def config_has_section(self):
        return self.section == 'DEFAULT' or self.config.has_section(self.section)

    @property
    def config_path(self) -> Optional[str]:
        for path in self.config_paths:
            if path is not None and isfile(path):
                return path

    @property
    def config_paths(self) -> list:
        return [
            self.env_path,
            self.current_directory_path,
            self.home_directory_path,
            self.system_directory_path
        ]

    @property
    def env_path(self) -> Optional[str]:
        env_value = os.getenv('TARENTULA_CONFIG', None)
        if env_value is not None:
            return os.path.abspath(env_value)

    @property
    def home_directory_path(self) -> str:
        return join(Path.home(), '.tarentula.ini')

    @property
    def current_directory_path(self) -> str:
        return join(os.getcwd(), 'tarentula.ini')

    @property
    def system_directory_path(self) -> str:
        return '/etc/tarentua/tarentua.ini'
