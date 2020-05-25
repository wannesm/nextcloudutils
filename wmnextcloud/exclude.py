# encoding: utf-8
"""
Exclude patterns for Nextcloud (stored in sync-exclude.lst files).

Created by Wannes Meert.
Copyright (c) 2020 KU Leuven. All rights reserved.
"""
import fnmatch
import logging
from pathlib import Path
import platform


logger = logging.getLogger("be.wannesm.wmnextcloud")


class Exclude:
    def __init__(self, path=None, ignore_exclude_pattern=None, ignore_global=False):
        self.patterns = []
        self.local_sync_exclude_list_path = None
        if ignore_exclude_pattern is None:
            self.ignore_exclude_pattern = set()
        else:
            self.ignore_exclude_pattern = ignore_exclude_pattern
        # Local excludes
        if path is not None and path.exists():
            self.local_sync_exclude_list_path = path
            logger.debug(f'Using local sync-exclude.lst file: {path}')
            with path.open("r") as fp:
                for line in fp.readlines():
                    self.parse_line(line)
            self.base = str(path.parent)
        # Global excludes
        if not ignore_global:
            global_exc_fn = self.global_sync_exclude_list_path()
            logger.debug(f'Using global sync-exclude.lst file: {global_exc_fn}')
            if global_exc_fn is not None and global_exc_fn.exists():
                with global_exc_fn.open("r") as fp:
                    for line in fp.readlines():
                        self.parse_line(line)

    @staticmethod
    def global_sync_exclude_list_path():
        if platform.system() == 'Darwin':
            global_exc_fn = Path.home() / 'Library' / 'Preferences' / 'Nextcloud' / 'sync-exclude.lst'
        else:
            global_exc_fn = None
        return global_exc_fn

    def parse_line(self, line):
        if line[0] == "]":
            line = line[1:]
        line = line.strip()
        if line in self.ignore_exclude_pattern:
            return
        self.patterns.append(line)

    def excluded_path(self, path):
        path = str(path)
        if self.base is not None:
            if self.base != path[:len(self.base)]:
                raise AttributeError(f'Path does not start with base ({self.base}): {path}')
            path = path[len(self.base):]
        for patn in self.patterns:
            if fnmatch.fnmatch(path, patn):
                return True
        return False

    def excluded_paths(self, paths):
        names = [path.name for path in paths]
        exc_names = []
        for patn in self.patterns:
            exc_names += fnmatch.filter(names, patn)
        return exc_names
