"""
SftpMan
=======

SftpMan is a command-line and GUI application that makes it easy to setup and mount SSHFS/SFTP file systems.

It allows you to setup all your SFTP systems using a GUI and easily mount/unmount them (from the GUI or the CLI).
"""

from setuptools import setup

setup(
    name = "SftpMan",
    version = '0.1.3',
    description = "A command-line and GTK application that helps you mount SFTP file systems.",
    long_description = __doc__,
    author = "Slavi Pantaleev",
    author_email = "s.pantaleev@gmail.com",
    url = "https://github.com/spantaleev/SftpMan",
    keywords = ["sftp", "ssh", "sshfs", "gtk"],
    license = "BSD",
    packages = ['sftpman'],
    entry_points="""
    [console_scripts]
    sftpman = sftpman.launcher:main
    """,
    zip_safe = False,
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Topic :: Communications :: File Sharing",
        "Topic :: Desktop Environment :: File Managers",
        "Topic :: Desktop Environment :: Gnome",
        "Topic :: Internet",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Topic :: System :: Networking",
        "Topic :: Utilities"
    ]
)
