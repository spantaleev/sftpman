"""
SftpMan
=======

SftpMan is a command-line application (with a GUI frontend packaged separately) that makes it easy to setup and mount SSHFS/SFTP file systems.

It allows you to define all your SFTP systems and easily mount/unmount them.

A GTK frontend is available, named sftpman-gtk.
"""

from setuptools import setup

setup(
    name = "sftpman",
    version = '0.5.4',
    description = "A command-line application that helps you mount SFTP file systems.",
    long_description = __doc__,
    author = "Slavi Pantaleev",
    author_email = "s.pantaleev@gmail.com",
    url = "https://github.com/spantaleev/sftpman",
    keywords = ["sftp", "ssh", "sshfs"],
    license = "BSD",
    packages = ['sftpman'],
    entry_points="""
    [console_scripts]
    sftpman = sftpman.launcher:main
    """,
    zip_safe = False,
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Topic :: Communications :: File Sharing",
        "Topic :: Internet",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Topic :: System :: Networking",
        "Topic :: Utilities"
    ]
)
