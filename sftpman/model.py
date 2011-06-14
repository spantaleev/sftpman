#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement
import re
from helper import json, shell_exec
from exception import SftpConfigException

SSH_PORT_DEFAULT = 22

class EnvironmentModel(object):
    """A configuration object that represents the environment
    with which we're now working.
    """

    def __init__(self):
        import os
        self.mount_path_base = '/mnt/sshfs/'
        self.config_path_base = os.path.expanduser('~/.config/sftpman/')
        self.config_path_mounts = '%smounts/' % self.config_path_base

    def get_system_config_path(self, system_id):
        return '%s%s.js' % (self.config_path_mounts, system_id)

    def get_system_mount_dest(self, system_id):
        """The local path where the system will be mounted."""
        return '%s%s' % (self.mount_path_base, system_id)

    def is_mounted(self, system_id):
        return system_id in self.get_mounted_ids()

    def get_pid_by_system_id(self, system_id):
        # Looking for `username {PID} blah blah {mount_dest}`
        mount_dest = self.get_system_mount_dest(system_id)
        regex = re.compile("^(?:\w+)\s+(\d+)\s+(?:.+?)%s$" % re.escape(mount_dest))

        processes = shell_exec("/bin/ps ux | /bin/grep '/usr/bin/sshfs'")
        for line in processes.split("\n"):
            match_object = regex.match(line)
            if match_object is None:
                continue
            return int(match_object.group(1))
        return None

    def get_available_ids(self):
        cfg_files = shell_exec('/bin/ls %s' % self.config_path_mounts).strip().split('\n')
        return [file_name[0:-3] for file_name in cfg_files if file_name.endswith('.js')]

    def get_mounted_ids(self):
        # Looking for /mnt/sshfs/{id}
        regex = re.compile("/usr/bin/sshfs(?:.+?)%s(\w+)$" %
                           re.escape(self.mount_path_base))

        processes = shell_exec("/bin/ps ux | /bin/grep '/usr/bin/sshfs'")
        ids = []
        for line in processes.split("\n"):
            if self.mount_path_base not in line:
                continue
            match_object = re.search(regex, line)
            if (match_object is None):
                continue
            ids.append(match_object.group(1))
        return ids

    def get_unmounted_ids(self):
        ids_mounted = self.get_mounted_ids()
        return [id for id in self.get_available_ids() if id not in ids_mounted]


class SystemModel(object):
    """Represents a system (mount point) that sftpman manages."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.host = kwargs.get('host', None)
        self.port = int(kwargs.get('port', SSH_PORT_DEFAULT))
        self.user = kwargs.get('user', None)
        self.mount_opts = list(kwargs.get('mountOptions', []))
        self.mount_point = kwargs.get('mountPoint', None)
        self.ssh_key = kwargs.get('sshKey', None)
        self.cmd_before_mount = kwargs.get('beforeMount', None)

    def validate(self):
        def is_alphanumeric(value):
            # Well, not really alphanumeric, but close enough to call it that
            return re.compile('^[a-zA-Z0-9\.\-]+$').match(value) is not None

        def is_valid_path(value):
            return re.compile('^(/[a-zA-Z0-9\.\-]+)+/?$').match(value) is not None

        errors = []
        if not is_alphanumeric(self.id):
            errors.append(('id', 'IDs can only contain letters, digits, dot and dash.'))
        if not is_alphanumeric(self.host):
            errors.append(('host', 'Hosts can only contain letters, digits, dot and dash.'))
        if not is_valid_path(self.mount_point):
            errors.append(('mount_point', 'Invalid remote mount point.'))
        if not is_valid_path(self.ssh_key):
            errors.append(('mount_point', 'Invalid ssh key path.'))
        if not is_alphanumeric(self.user):
            errors.append(('user', 'Usernames can only contain letters and digits.'))
        try:
            port = int(self.port)
            if not(0 <= port <= 65535):
                raise ValueError('Bad port range.')
        except ValueError:
            errors.append(('port', 'Ports need to be numbers between 0-65535.'))
        if not isinstance(self.mount_opts, list):
            errors.append(('mount_opts', 'Bad options received.'))
        if not isinstance(self.cmd_before_mount, basestring):
            errors.append(('cmd_before_mount', 'Invalid before mount command.'))

        return (len(errors) == 0, errors)

    def export(self):
        """Serializes to JSON."""
        fields = ['id', 'host', 'port', 'user']
        out = {}
        for field in fields:
            out[field] = getattr(self, field, None)
        out['mountOptions'] = self.mount_opts
        out['mountPoint'] = self.mount_point
        out['beforeMount'] = self.cmd_before_mount
        return json.dumps(out)

    @staticmethod
    def create_by_id(id, environment):
        path = environment.get_system_config_path(id)
        return SystemModel.create_from_file(path)

    @staticmethod
    def create_from_file(path):
        try:
            with open(path) as f:
                config = json.loads(f.read())
                return SystemModel(**config)
        except (ValueError, IOError), e:
            raise SftpConfigException('Failed finding or parsing config.', e)
