SftpMan with the GTK frontend
=============================

.. image:: https://github.com/spantaleev/sftpman-gtk/raw/master/sftpman-gui.png

---------------------------------------

SftpMan consists of a Command Line and a GTK application (packaged separately) that make it simpler to setup and mount SSHFS/SFTP file systems.

The idea was to develop a simple CLI/GUI application for Linux that can be used to manage SFTP systems.

It relies on `sshfs`_ to do all the mounting work.
SftpMan allows you to setup many remote filesystems and helps you easily mount/unmount them.

Every system managed by SftpMan is identified by an id such as ``my-machine``, which is used in file paths and when managing the system.

Configuration data is stored in ``~/.config/sftpman/`` as JSON files.

All systems are mounted under ``/mnt/sshfs/``. For the ``my-machine`` machine, that would be ``/mnt/sshfs/my-machine``.

---------------------------------------

Installing on ArchLinux
-----------------------

On `ArchLinux`_, there's an official `sftpman AUR package`_. To install using ``yaourt``::

    yaourt -S sftpman

The package takes care of all dependencies and SftpMan should be able to start.

Optional dependencies will be suggested to you upon install.

Installing on other distributions
---------------------------------

For other distributions you can install using **pip**::

    pip install sftpman

You also need to install `sshfs`_ yourself.

CLI Application
---------------

The CLI application (``sftpman`` executable) supports the following commands::

    help:
     - Displays this help menu.

    ls:
     - Lists the available/mounted/unmounted sftp systems.
            Usage: sftpman ls {what}
            Where {what} is one of: available, mounted, unmounted

    mount:
     - Mounts the specified sftp system, unless it's already mounted.
            Usage: sftpman mount {id}..

    mount_all:
     - Mounts all sftp file systems known to sftpman.
            Usage: sftpman mount_all

    preflight_check:
     - Detects whether we have everything needed to mount sshfs filesystems.

    rm:
     - Removes a system by id.
            Usage: sftpman rm {system_id}..
            For a list of system ids, see `sftpman ls available`.

    setup:
     - Defines a new sftp file system configuration or edits an old one with the same id.
            Usage: sftpman setup {options}
            Available {options}:
                --id={unique system identifier}
                    You use this to recognize and manage this sftp system.
                    It determines what the local mount point is.
                    If `--id=example`, the filesystem will be mounted to: `/mnt/sshfs/example`
                --host={host to connect to}
                --port={port to connect to} [default: 22]
                --user={username to authenticate with} [default: current user]
                --mount_opt={option to pass to sshfs} [optional] [can be passed more than once]
                    Example: --mount_opt="follow_symlinks" --mount_opt="workaround=rename"
                    `sshfs --help` tells you what sshfs options are available
                --mount_point={remote path to mount}
                --auth_method={method}
                    Specifies the authentication method.
                    Can be `password` or `publickey`. [default: publickey]
                --ssh_key={path to the ssh key to use for authentication}
                    Only applies if auth_method is `publickey`.
                --cmd_before_mount={command to run before mounting} [default: /bin/true]
                    Allows you to run a custom command every time this system is mounted.

    unmount:
     - Unmounts the specified sftp system.
            Usage: sftpman unmount {id}..

    unmount_all:
     - Unmounts all sftp file systems known to sftpman.
            Usage: sftpman unmount_all


GUI Application
---------------

`sftpman-gtk`_ is a GTK frontend for sftpman, which is packaged separately.
Installing the frontend automatically installs the CLI application as a dependency.


Dependencies
------------

- `sshfs`_
- Python 2.7+


Known limitations
-----------------

- Doesn't support mounting in a location different than ``/mnt/sshfs/``


.. _sshfs: http://fuse.sourceforge.net/sshfs.html
.. _ArchLinux: http://www.archlinux.org/
.. _AUR: https://wiki.archlinux.org/index.php/AUR
.. _sftpman AUR package: http://aur.archlinux.org/packages.php?ID=49211
.. _sftpman-gtk: https://github.com/spantaleev/sftpman-gtk
