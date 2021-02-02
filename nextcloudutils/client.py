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
from .config import use_config
from .exception import NoNextcloudDirectory


logger = logging.getLogger("be.wannesm.wmnextcloud")


class Client:
    def __init__(self, config, ignore_global=False, cwd=None):
        self.config = use_config(config)
        self.webdav = WebDAV(self.config)
        self.exclude_kwargs = {
            'ignore_exclude_pattern': self.config.ignore_exclude_pattern,
            'ignore_global': ignore_global
        }
        self.exclude = None
        self.cwd = None  # relative to Nextcloud root
        self.set_cwd(cwd)

    def path_in_localdir(self, path):
        """Return list of directory names that is the path in the local nextcloud directory.
        Returns None if the given path is not in the Nextcloud directory.

        :param path:
        :return: List of directory names forming the path or None
        """
        path = Path(path)
        rootpath = Path("/")
        npath = path.resolve()
        opath = self.config.local_dir.resolve()
        relpath = []
        path_in_nc_dir = (npath == opath)
        while npath != rootpath and not path_in_nc_dir:
            relpath.append(npath.name)
            npath = npath.parent
            path_in_nc_dir = (npath == opath)
        if path_in_nc_dir:
            relpath.reverse()
            return relpath
        return None

    def set_cwd(self, path=None):
        if path is None:
            # Reset
            self.cwd = None
            self.exclude = Exclude(**self.exclude_kwargs)
            logger.debug(f'Set CWD to Nextcloud directory: {self.local_dir}')
            return
        relpath = self.path_in_localdir(path)
        if relpath is None:
            raise NoNextcloudDirectory(
                f'Path needs to be in the Nextcloud directory: {self.config.local_dir}, got {path}')
        dpath = '/'.join(relpath)
        self.cwd = self.config.local_dir / dpath
        self.webdav.cwd = dpath
        logger.debug(f'Set CWD to {dpath} - local CWD: {self.cwd}')
        local_exclude = self.find_parent_local_sync_exclude_files(self.cwd)
        if local_exclude is not None:
            logger.debug(f'Using local exclude files:')
            for local_exclude_file in local_exclude:
                logger.debug(f'- {local_exclude_file}')
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
        return self._find_children_local_sync_exclude_files_inner(self.local_dir, exclude=self.exclude,
                                                                  max_depth=max_depth, only_exclude_files=True)

    def find_children_local_sync_exclude_files(self, max_depth=None):
        if max_depth is None:
            max_depth = self.config.max_depth
        return self._find_children_local_sync_exclude_files_inner(self.local_dir, exclude=self.exclude,
                                                                  max_depth=max_depth)

    def _find_children_local_sync_exclude_files_inner(self, path, exclude=None, depth=0, max_depth=None,
                                                      only_exclude_files=False):
        if depth > max_depth:
            logger.debug(f'- Searching path: {path} -- Max depth, stopped')
            return
        logger.debug(f'- Searching path: {path}')
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
                yield from self._find_children_local_sync_exclude_files_inner(fn, exclude=exclude, depth=depth + 1, max_depth=max_depth,
                                                                              only_exclude_files=only_exclude_files)

    def find_parent_local_sync_exclude_files(self, path):
        inc_files = []
        path = Path(path)
        rootpath = Path("/")
        npath = path.resolve()
        opath = self.config.local_dir.resolve()
        relpath = []
        path_in_nc_dir = (npath == opath)
        cur_fn = path / ".sync-exclude.lst"
        if cur_fn.exists():
            inc_files.append(cur_fn)
        while npath != rootpath and not path_in_nc_dir:
            relpath.append(npath.name)
            npath = npath.parent
            cur_fn = npath / ".sync-exclude.lst"
            if cur_fn.exists():
                inc_files.append(cur_fn)
            path_in_nc_dir = (npath == opath)
        if path_in_nc_dir:
            return inc_files
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

    @classmethod
    def get_local_size(cls, path):
        path = Path(path)
        if path.is_file():
            return path.stat().st_size
        total_size = 0
        for child_path in path.iterdir():
            total_size += cls.get_local_size(child_path)
        return total_size
