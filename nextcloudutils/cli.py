# encoding: utf-8
"""

Created by Wannes Meert.
Copyright (c) 2020 KU Leuven. All rights reserved.
"""
import sys
import logging
import argparse
import subprocess as sp
from pathlib import Path


from .client import Client
from .exception import NoNextcloudDirectory
from .config import Config


logger = logging.getLogger("be.wannesm.wmnextcloud")
VERBOSE = logging.INFO - 5


def main(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)

    logger.setLevel(max(logging.INFO - 5 * (args.verbose - args.quiet), logging.DEBUG))
    logger.addHandler(logging.StreamHandler(sys.stdout))

    config = Config(Config.find_config_file(args.config))

    path = Path('.')
    if args.cwd is not None:
        path = args.cwd
    elif args.cwd_global:
        path = None
    try:
        client = Client(config=config, ignore_global=args.ignore_global, cwd=path)
    except NoNextcloudDirectory as exc:
        print(exc)
        sys.exit(1)

    cmd_map = {
        'log': cmd_log,
        'l': cmd_log,
        'ignored': cmd_ignored,
        'i': cmd_ignored,
        'patterns': cmd_exclude,
        'p': cmd_exclude
    }
    try:
        cmd_map[args.command](args, client)
    except KeyError:
        parser.print_help(sys.stderr)
        sys.exit(1)

def cmd_log(args, client):
    if args.app:
        cmd = [args.app, client.log_path]
        sp.call(cmd)
    else:
        print(client.log_path)


def cmd_ignored(args, client):
    depth = client.config.max_depth
    if args.depth is not None:
        depth = args.depth
    logger.info(f"Searching for all ignored files (max-depth={depth})")
    local_paths = list(client.find_children_local_sync_exclude_files(max_depth=depth))
    logger.info(f'Found {len(local_paths)} ignored files or directories')
    if args.no_remote or args.show_ignored:
        if args.sort_size:
            size_path = []
            for path in local_paths:
                size = client.get_local_size(path)
                size_path.append((size, path))
            size_path.sort(reverse=True)
            for size, path in size_path:
                readable_size = size / 1024 ** 2
                print(f'{size:>10} {readable_size:6,.0f}MiB {path}')
        else:
            for path in local_paths:
                size = client.get_local_size(path)
                readable_size = size / 1024**2
                print(f'{size:>10} {readable_size:6,.0f}MiB {path}')

    if not args.no_remote and len(local_paths) > 0:
        logger.info('Checking on remote')
        exist_paths = list(client.filter_exists_on_remote(local_paths))
        if len(exist_paths) == 0:
            logger.info("No ignored files found on remote server")
            return

        logger.info(f'Found {len(exist_paths)} ignored files or directories on remote')
        _, rpaths = zip(*exist_paths)
        if args.dry_run or logger.isEnabledFor(VERBOSE):
            if args.sort_size:
                size_path = []
                for lpath, rpath in exist_paths:
                    size = client.get_local_size(lpath)
                    size_path.append((size, lpath, rpath))
                size_path.sort(reverse=True)
                for size, lpath, rpath in size_path:
                    readable_size = size / 1024 ** 2
                    print(f'{size:>10} {readable_size:6,.0f}MiB {lpath}')
                    print(' ' * 21 + rpath)
            else:
                for lpath, rpath in exist_paths:
                    size = client.get_local_size(lpath)
                    readable_size = size / 1024 ** 2
                    print(f'{size:>10} {readable_size:6,.0f}MiB {lpath}')
                    print(' '*21 + rpath)
            if args.dry_run:
                return

        logger.info('Delete ignored files if they are present on remote')
        client.delete_remote_paths(rpaths, force=args.force)


def cmd_exclude(args, client):
    if args.paths:
        path = client.exclude.global_sync_exclude_list_path()
        if path is not None:
            print(f'Global file: {path}')
        paths = client.exclude.local_sync_exclude_list_paths
        if paths is not None:
            first = True
            for path in paths:
                if first:
                    print(f'Local files: {path}')
                else:
                    first = False
                    print(' '*13 + f'{path}')
        return

    if args.edit:
        cmd = [args.edit, client.exclude.global_sync_exclude_list_path()]
        sp.call(cmd)
        return

    if args.paths_children:
        for path in client.get_local_sync_exclude_files():
            print(path)
        return

    if args.edit_local:
        cmd = [args.edit_local, '.sync-exclude.lst']
        sp.call(cmd)
        return

    for pattern in client.exclude.patterns:
        print(pattern)


def create_parser():
    parser = argparse.ArgumentParser(description='Nextcloud utilities')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Verbose output')
    parser.add_argument('--quiet', '-q', action='count', default=0, help='Quiet output')
    parser.add_argument('--config',
                        help='Config YAML file')
    parser.add_argument('--cwd-global', '-g', action='store_true',
                        help='Run with Nextcloud root directory as working directory')
    parser.add_argument('--cwd', help='Set current working directory (default is current directory)')
    parser.add_argument('--ignore-global', action='store_true',
                        help='Ignore global sync-exclude.lst file')

    subparsers = parser.add_subparsers(help='Utility commands', dest="command")

    # Ignore
    parser_ignore = subparsers.add_parser('ignored', help='Search for ignored files',
                                          aliases=['i'])
    parser_ignore.add_argument('--dry-run', action='store_true', help='Do not delete files')
    parser_ignore.add_argument('--force', action='store_true', help='Force delete files')
    parser_ignore.add_argument('--no-remote', action='store_true', help='Only perform local search')
    parser_ignore.add_argument('--show-ignored', action='store_true', help='Show all ignored paths')
    parser_ignore.add_argument('--sort-size', action='store_true', help='Sort ignore paths by size')
    parser_ignore.add_argument('--depth', '-d', type=int, help='Search up to this depth')

    # Log
    parser_log = subparsers.add_parser('log', help='Nextcloud logs',
                                       aliases=['l'])
    parser_log.add_argument('--app', type=str, help='Open log with this binary')

    # Exclude
    parser_log = subparsers.add_parser('patterns', help='Filename patterns in sync-exclude.lst file(s)',
                                       aliases=['p'])
    parser_log.add_argument('--edit', type=str, help='Edit global sync-exclude.lst with this binary')
    parser_log.add_argument('--edit-local', type=str,
                            help='Edit local sync-exclude.lst with this binary (create file if it does not exist)')
    parser_log.add_argument('--paths', action='store_true',
                            help='Show paths for all global and local .sync-exclude.lst files')
    parser_log.add_argument('--paths-children', action='store_true',
                            help='Search all local .sync-exclude.lst files found in the NextCloud directory')

    return parser
