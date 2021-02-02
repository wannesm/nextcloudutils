# encoding: utf-8
"""
Remote connection for Nextcloud.

Based on https://github.com/ezhov-evgeny/webdav-client-python-3

Created by Wannes Meert.
Copyright (c) 2020 KU Leuven. All rights reserved.
"""
import logging

from webdav3.client import Client
from webdav3.exceptions import RemoteResourceNotFound

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x):
        return x

from .config import use_config


logger = logging.getLogger("be.wannesm.wmnextcloud")


class WebDAV:
    def __init__(self, config):
        self._client = None
        self.config = use_config(config)
        self.cwd = None

    @property
    def local_dir(self):
        if self.cwd is None:
            return self.config.local_dir
        return self.config.local_dir / self.cwd

    @property
    def remote_dir(self):
        if self.cwd is None:
            return self.config.remote_dir
        return self.config.remote_dir / self.cwd

    def filter_exists_on_remote(self, paths):
        local_dir = str(self.local_dir)
        for path in tqdm(paths):
            path = str(path)
            if path[:len(local_dir)] != local_dir:
                raise Exception(f'Local path does not start with local_dir: {path}')
            rpath = str(self.remote_dir / path[len(local_dir) + 1:])
            logger.debug(f'Checking: {rpath}')
            # exists = self.client.check(rpath)
            try:
                info = self.client.info(rpath)
                logger.debug(info)
                yield path, rpath
            except RemoteResourceNotFound:
                pass

    def delete_remote_paths(self, paths, force=False, log=True):
        if not force:
            answer = input("Are you sure you want to remove these paths on the server [yN]: ")
            if answer != "y":
                print('Cancelled')
                return
        if log:
            with (self.config.cwd / "delete_remote_paths.log").open("a") as fp:
                self._delete_remote_paths_inner(paths, fp)
        else:
            self._delete_remote_paths_inner(paths)

    def _delete_remote_paths_inner(self, paths, fp=None):
        for path in tqdm(paths):
            logger.debug(f'Deleting: {path}')
            if fp:
                fp.write(f'Deleting: {path}\n')
            try:
                self.client.clean(path)
            except RemoteResourceNotFound:
                logger.warning(f'Path not found: {path}')
                if fp:
                    fp.write(f'Path not found: {path}')

    @property
    def client(self):
        if self._client is None:
            options = {
                'webdav_hostname': self.config.hostname,
                'webdav_login': self.config.username,
                'webdav_password': self.config.password
            }
            self._client = Client(options)
        return self._client
