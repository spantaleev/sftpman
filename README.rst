SftpMan
=======

.. image:: https://github.com/spantaleev/SftpMan/raw/master/sftpman-gui.png

---------------------------------------

SftpMan consists of a Command Line and a GTK application that make it simpler to setup and mount SSHFS/SFTP file systems.

The idea was to develop a simple GUI program for Linux that can be used to manage SFTP systems.

It relies on `sshfs`_ to do all the mounting work.
SftpMan allows you to setup many remote filesystems and helps you easily mount/unmount them.

Every managed by SftpMan system is identified by an id as "my-machine", which is used in file paths and when managing the system.

Configuration data is stored in ``~/.config/sftpman/`` as JSON files.

All systems are mounted under ``/mnt/sshfs/``. For the "my-machine" machine, that would be ``/mnt/sshfs/my-machine``.

---------------------------------------

Installing
----------

Installing using **pip** is possible::

    pip install sftpman

You'll need to install ``pygtk`` manually, but maybe you already have that installed.
Installing ``pygtk`` from **pip** would not work, because some of its dependencies are not available there.

You also need to install `sshfs`_ yourself.

If the SSH keys that you'll use for authentication are password-protected (as they should be)
and you want the GUI Application to prompt you for a password,
you may need to install the `openssh-askpass` package (or whatever it's called) for your distribution.
Some distributions have that installed by default.

GUI (GTK) Application
---------------------

Launching the main file (sftpman.py) with command line arguments launches the GUI.
Only the GUI currently supports adding/editing/removing of sftp systems.

In order to setup an sftp system for further use (mounting/unmounting) you need to specify:

- Hostname/IP
- Port (defaults to 22)
- Remote username/login
- SSH private key (you need its corresponding public key added to the remote user's .authorized_keys file)
- Remote mount point (the remote directory you want mounted on your system)
- Options (options to pass to sshfs if you want something more advanced)
- Run before mount (a command to execute before mounting)

We currently don't (and probably never will) support mounting by using passwords (instead of keys).

If your SSH private key requires a password to use (as it should), you'll be asked for it.

The "Run before mount" command allows you to do whatever init stuff you want.
I'm using it to initialize my ssh-agent (by adding my key there), so that I only have to type in the key password once.


CLI Application
---------------

Launching the main file (sftpman) with at least one additional command line argument will launchy CLI mode.
What we support in the CLI is fairly limited, but it's still at least a bit usable (as you can see in the ``sleep.d/49-sftpman`` script).

It can do mounting/unmounting and listing at the moment. It outputs results as JSON.

Launch ``sftpman help`` to see the exact commands it offers.


Dependencies
------------

- `sshfs`_
- Python 2.6+
- PyGTK for the GUI application


Known limitations
-----------------

- Doesn't support password authentication, only SSH keys
- Doesn't support all of the functionality in CLI mode - certain things require the GUI to be used
- Doesn't do any validation on the data you provide in the GUI
- Doesn't support mounting in a location different than ``/mnt/sshfs/``
- All logic runs in the GUI thread, which can make the GUI freeze for a while


.. _sshfs: http://fuse.sourceforge.net/sshfs.html
