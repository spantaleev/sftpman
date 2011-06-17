SftpMan
=======

.. image:: https://github.com/spantaleev/sftpman-gtk/raw/master/sftpman-gui.png

SftpMan with the GTK frontend.

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

Launching the main file (sftpman) with at least one additional command line argument will launch CLI mode.
The CLI application supports the following commands::

    help:
    - Shows a help menu

    ls:
     - Lists the available/mounted/unmounted sftp systems.

            Usage: sftpman ls {what}
            Where {what} is one of: available, mounted, unmounted


    mount:
     - Mounts the specified sftp system, unless it's already mounted.

            Usage: sftpman mount {id}


    mount_all:
     - Mounts all sftp file systems known to sftpman.

            Usage: sftpman mount_all


    preflight_check:
     - Detects whether we have everything needed to mount sshfs filesystems.


    unmount:
     - Unmounts the specified sftp system.

            Usage: sftpman unmount {id}


    unmount_all:
     - Unmounts all sftp file systems known to sftpman.

            Usage: sftpman unmount_all

Launch ``sftpman help`` to see the exact commands it offers.


GUI Application
---------------

There's a GTK frontend for sftpman, which is packaged separately.
Look for ``sftpman-gtk``.


Dependencies
------------

- `sshfs`_
- Python 2.6+


Known limitations
-----------------

- Doesn't support password authentication, only SSH keys
- Doesn't support mounting in a location different than ``/mnt/sshfs/``


.. _sshfs: http://fuse.sourceforge.net/sshfs.html
.. _ArchLinux: http://www.archlinux.org/
.. _AUR: https://wiki.archlinux.org/index.php/AUR
.. _sftpman AUR package: http://aur.archlinux.org/packages.php?ID=49211
