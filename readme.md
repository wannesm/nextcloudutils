# Nextcloud Utilities

Command line utility for additional Nextcloud functionality.

## Installation and Usage

```
pip install nextcloudutils
nextcloudutils -h
```

If a configuration file `~/.config/nextcloudutils/config.yaml` exists, this will be used.
Alternatively a configuration file can be specified using `--config`.

```
cat ~/.config/nextcloudutils/config.yaml
webdav_hostname: https://nextcloud.example.com/remote.php/webdav/
webdav_login: user
webdav_password: null
local_dir: /Users/username/Nextcloud/
remote_dir: .
max_depth: 200
ignore_exclude_pattern:
  - .DS_Store
```

Note: it is recommended to set `webdav_password` to `null` such that it asks for a password.

## Functionality

### Patterns to ignore files globally and locally

Nextcloud keeps track of a list of global patterns to ignore files (i.e. files that should not be synced) in a `sync-exclude.lst` file.
Additionally, you can add local `sync-exclude.lst` files to ignore files only in a subtree of your Nextcloud directory.

To get an overview of all `sync-exclude.lst` files:

```
nextcloudutils patterns --paths  # Pattern files used
nextcloudutils patterns --paths-children  # Local pattern files in this directory
```

To see all patterns that are used to ignore files (combining global and local file(s)):

```
nextcloudutils patterns
```

### Edit pattern file

To quickly edit `sync-exclude.lst` files:

```
nextcloudutils patterns --edit vim        # Edit global file with vim
nextcloudutils patterns --edit-local vim  # Edit or create local file with vim
```

### Ignored files

Get an overview of all local files and directories that are ignored:

```
nextcloudutils ignored --no-remote --show-ignored --sort-size
```

Sometimes the Nextcloud sync is off and the server contains files that should have not been synced.
Since this can be taken up valueble storage space, you can automatically delete those directories from the server using:

```
nextcloudutils ignored --dry-run  # If you first want to see which files and directories would be deleted
nextcloudutils ignored
```

