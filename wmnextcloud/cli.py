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


logger = logging.getLogger("be.wannesm.wmnextcloud")
default_config_path = Path(__file__).parent.parent / 'config.yaml'


def main(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)

    logger.setLevel(max(logging.INFO - 10 * (args.verbose - args.quiet), logging.DEBUG))
    logger.addHandler(logging.StreamHandler(sys.stdout))

    path = None
    if args.local:
        path = Path('.')
    client = Client(config=args.config, ignore_global=args.ignore_global, cwd=path)

    cmd_map = {
        'log': cmd_log,
        'l': cmd_log,
        'ignore': cmd_ignore,
        'i': cmd_ignore,
        'exclude': cmd_exclude,
        'e': cmd_exclude
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


def cmd_ignore(args, client):
    logger.info(f"Searching for all ignored files (max-depth={client.config.max_depth})")
    local_paths = list(client.find_sync_exclude_files())
    logger.info(f'Found {len(local_paths)} ignored files or directories')
    if args.no_remote:
        for path in local_paths:
            print(path)
        return

    logger.info('Checking on remote')
    exist_paths = list(client.filter_exists_on_remote(local_paths))
    if len(exist_paths) == 0:
        logger.info("No ignored files found on remote server")
        return
    logger.info(f'Found {len(exist_paths)} ignored files or directories on remote')
    _, rpaths = zip(*exist_paths)
    if args.dry_run:
        for path in rpaths:
            print(path)
        return

    logger.info('Delete ignored files if they are present on remote')
    client.delete_remote_paths(rpaths, force=args.force)


def cmd_exclude(args, client):
    if args.path:
        path = client.exclude.global_sync_exclude_list_path()
        if path is not None:
            print(f'Global: {path}')
        path = client.exclude.local_sync_exclude_list_path
        if path is not None:
            print(f'Local:  {path}')
        return

    if args.app:
        cmd = [args.app, client.exclude.global_sync_exclude_list_path()]
        sp.call(cmd)
        return

    if args.children:
        for path in client.get_local_sync_exclude_files():
            print(path)
        return

    if args.app_local:
        cmd = [args.app_local, '.sync-exclude.lst']
        sp.call(cmd)
        return

    for pattern in client.exclude.patterns:
        print(pattern)


def create_parser():
    parser = argparse.ArgumentParser(description='Nextcloud utilities')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Verbose output')
    parser.add_argument('--quiet', '-q', action='count', default=0, help='Quiet output')
    parser.add_argument('--config', default=default_config_path,
                        help='Config YAML file')
    parser.add_argument('--local', '-l', action='store_true',
                        help='Run from current directory, otherwise run from Nextcloud root directory')
    parser.add_argument('--ignore-global', action='store_true',
                        help='Ignore global sync-exclude.lst file')

    subparsers = parser.add_subparsers(help='Utility commands', dest="command")

    # Ignore
    parser_ignore = subparsers.add_parser('ignore', help='Deal with ignored files',
                                          aliases=['i'])
    parser_ignore.add_argument('--dry-run', action='store_true', help='Do not delete files')
    parser_ignore.add_argument('--force', action='store_true', help='Force delete files')
    parser_ignore.add_argument('--no-remote', action='store_true', help='Only perform local search')

    # Log
    parser_log = subparsers.add_parser('log', help='Log files',
                                       aliases=['l'])
    parser_log.add_argument('--app', type=str, help='Open log with this binary')

    # Exclude
    parser_log = subparsers.add_parser('exclude', help='Global sync-exclude.lst patterns',
                                       aliases=['e'])
    parser_log.add_argument('--app', type=str, help='Open sync-exclude.lst with this binary')
    parser_log.add_argument('--app-local', type=str,
                            help='Open local sync-exclude.lst with this binary (create if it does not exist)')
    parser_log.add_argument('--path', action='store_true', help='Show path')
    parser_log.add_argument('--children', action='store_true', help='Print all local .sync-exclude.lst files')

    return parser
