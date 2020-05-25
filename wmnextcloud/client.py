# encoding: utf-8
"""
Local client for Nextclould.

Created by Wannes Meert.
Copyright (c) 2020 KU Leuven. All rights reserved.
"""
import logging
from pathlib import Path
import platform

from .exclude import Exclude
from .webdav import WebDAV
from .config import Config


logger = logging.getLogger("be.wannesm.wmnextcloud")


class Client:
    def __init__(self, config, ignore_global=False, cwd=None):
        self.config = Config(config)
        self.webdav = WebDAV(config)
        self.exclude_kwargs = {
            'ignore_exclude_pattern': self.config.ignore_exclude_pattern,
            'ignore_global': ignore_global
        }
        self.exclude = None
        self.cwd = None  # relative to Nextcloud root
        self.set_cwd(cwd)

    def set_cwd(self, path=None):
        if path is None:
            # Reset
            self.cwd = None
            self.exclude = Exclude(**self.exclude_kwargs)
            logger.debug(f'Set CWD to Nextcloud directory: {self.local_dir}')
            return
        npath = str(path.absolute())
        opath = str(self.config.local_dir)
        if npath[:len(opath)] != opath:
            raise AttributeError(f'Path needs to be in the Nextcloud directory: {self.config.local_dir}, got {path}')
        dpath = npath[len(opath) + 1:]
        self.cwd = dpath
        self.webdav.cwd = dpath
        logger.debug(f'Set CWD to {self.local_dir}')
        local_exclude = self.find_parent_sync_include_file(self.local_dir)
        if local_exclude is not None:
            logger.debug(f'Using local sync-exclude.lst file: {local_exclude}')
            self.exclude = Exclude(local_exclude, **self.exclude_kwargs)
        else:
            self.exclude = Exclude(**self.exclude_kwargs)

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

    def reset_cwd(self):
        self.cwd = None

    def get_local_sync_exclude_files(self, max_depth=None):
        if max_depth is None:
            max_depth = self.config.max_depth
        return self._find_sync_exclude_files_inner(self.local_dir, exclude=self.exclude,
                                                   max_depth=max_depth, only_exclude_files=True)

    def find_sync_exclude_files(self, max_depth=None):
        if max_depth is None:
            max_depth = self.config.max_depth
        return self._find_sync_exclude_files_inner(self.local_dir, exclude=self.exclude,
                                                   max_depth=max_depth)

    def _find_sync_exclude_files_inner(self, path, exclude=None, depth=0, max_depth=None,
                                       only_exclude_files=False):
        if depth > max_depth:
            logger.debug(f'- Path: {path} -- Max depth, stopped')
            return
        logger.debug(f'- Path: {path}')
        sync_exclude = path / '.sync-exclude.lst'
        if sync_exclude.exists():
            logger.debug(f"Reading sync-exclude file: {sync_exclude}")
            if only_exclude_files:
                yield sync_exclude
            exclude = Exclude(sync_exclude, **self.exclude_kwargs)
        fns = list(path.glob('*'))
        if exclude is not None:
            exc_names = exclude.excluded_paths(fns)
            if not only_exclude_files and len(exc_names) > 0:
                logger.debug(f'Found names to ignore:\n' + '\n'.join(str(p) for p in exc_names))
                for exc_fn in exc_names:
                    yield path / exc_fn
            exc_names = set(exc_names)
        else:
            exc_names = set()
        for fn in fns:
            if fn.is_dir() and fn.name not in exc_names:
                yield from self._find_sync_exclude_files_inner(fn, exclude=exclude, depth=depth+1, max_depth=max_depth,
                                                               only_exclude_files=only_exclude_files)

    def find_parent_sync_include_file(self, path):
        lpath = str(self.config.local_dir)
        while lpath in str(path):
            cur_fn = path / ".sync-exclude.lst"
            if cur_fn.exists():
                return cur_fn
            path = path.parent
        return None

    def filter_exists_on_remote(self, paths):
        return self.webdav.filter_exists_on_remote(paths)

    def delete_remote_paths(self, paths, force=False, log=True):
        return self.webdav.delete_remote_paths(paths, force=force, log=log)

    @property
    def log_path(self):
        if platform.system() == 'Darwin':
            return Path.home() / 'Library' / 'Application Support' / 'Nextcloud' / 'Nextcloud_sync.log'
        else:
            raise Exception(f'Not supported platform: {platform.system()}')
