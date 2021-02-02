# encoding: utf-8
"""
config.py

Created by Wannes Meert.
Copyright (c) 2020 KU Leuven. All rights reserved.
"""
from pathlib import Path
from getpass import getpass
import logging

from yaml import load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


logger = logging.getLogger("be.wannesm.wmnextcloud")


class Config:
    def __init__(self, config, cwd=None):
        if cwd is None:
            self.cwd = Path('.')
        else:
            self.cwd = cwd
        if isinstance(config, Config):
            self.config = config.config
            self.cwd = config.cwd
        elif type(config) is dict:
            self.config = config
        elif type(config) is str:
            logger.debug(f'Config file (str): {config}')
            config = Path(config)
            with config.open("r") as fp:
                self.config = load(fp, Loader=Loader)
        elif isinstance(config, Path):
            logger.debug(f'Config file (path): {config}')
            with config.open("r") as fp:
                self.config = load(fp, Loader=Loader)
        else:
            raise AttributeError("Cannot read config")
        self._ignore_exclude_pattern = None

    def get(self, key, default):
        return self._from_config(key, default)

    def _from_config(self, key, default=None):
        try:
            return self.config[key]
        except KeyError:
            return default

    @staticmethod
    def find_config_file(path=None):
        if path is not None:
            path = Path(path)
            logger.debug(f'Searching config file: {path}')
            if path.exists():
                logger.debug('... found')
                return path
            else:
                raise Exception(f'Configuration file not found: {path}')
        path = Path.home() / ".config" / "nextcloudutils" / "config.yaml"
        logger.debug(f'Searching config file: {path}')
        if path.exists():
            logger.debug('... found')
            return path
        path = Path(__file__).parent.parent / 'config.yaml'
        logger.debug(f'Searching config file: {path}')
        if path.exists():
            logger.debug('... found')
            return path
        return None

    @property
    def ignore_exclude_pattern(self):
        if self._ignore_exclude_pattern is None:
            self._ignore_exclude_pattern = set(self._from_config('ignore_exclude_pattern', []))
        return self._ignore_exclude_pattern

    @property
    def max_depth(self):
        return self._from_config('max_depth', 100)

    @property
    def local_dir(self):
        return Path(self._from_config('local_dir'))

    @property
    def remote_dir(self):
        rdir = self._from_config('remote_dir')
        if rdir is None:
            raise Exception('No remote_dir is defined in the config file. '
                            'Fill in a path or avoid remote with --no-remote.')
        rdir = Path(rdir)
        return rdir

    @property
    def hostname(self):
        return self._from_config('webdav_hostname')

    @property
    def username(self):
        return self._from_config('webdav_login')

    @property
    def password(self):
        if 'webdav_password' in self.config and self.config['webdav_password'] is not None:
            print("Using known password")
            return self.config['webdav_password']
        pw = getpass(f'Nextcloud password for {self.username}: ')
        return pw


def use_config(arg=None):
    if isinstance(arg, Config):
        return arg
    return Config(arg)
