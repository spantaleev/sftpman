# -*- coding: utf-8 -*-
from __future__ import with_statement
import re
from helper import json, shell_exec, mkdir_p, rmdir, kill_pid
from exception import SftpConfigException


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

    PORT_RANGE_MIN = 0
    PORT_RANGE_MAX = 65535

    SSH_PORT_DEFAULT = 22

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.host = kwargs.get('host', None)
        self.port = int(kwargs.get('port', SystemModel.SSH_PORT_DEFAULT))
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
            if not(SystemModel.PORT_RANGE_MIN <= port <= SystemModel.PORT_RANGE_MAX):
                raise ValueError('Bad port range.')
        except ValueError:
            msg = 'Ports need to be numbers between %d and %d.' % (
                self.PORT_RANGE_MIN,
                self.PORT_RANGE_MAX,
            )
            errors.append(('port', msg))
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
            msg = 'Failed finding or parsing config at %s.'
            raise SftpConfigException(msg % path, e)


class SystemControllerModel(object):
    """Controls a given system within the environment.
    The controller manages mounting, unmounting, cleaning up, etc.
    """

    SIGNAL_SIGTERM = 15
    SIGNAL_SIGKILL = 9

    #: Time to wait when unmounting before forcefully killing the mount process
    KILL_WAIT_TIME_SECONDS = 2

    def __init__(self, system, environment):
        self.system = system
        self.environment = environment

    @property
    def mounted(self):
        return self.environment.is_mounted(self.system.id)

    @property
    def mount_point_local(self):
        return self.environment.get_system_mount_dest(self.system.id)

    @property
    def mount_point_remote(self):
        return self.system.mount_point

    def _mount_point_local_create(self):
        """Ensures the mount location exists, so we can start using it."""

        # Ensure nothing's mounted there right now..
        shell_exec("/bin/fusermount -u %s 2>&1" % self.mount_point_local)

        # Ensure the directory path exists
        mkdir_p(self.mount_point_local)

    def _mount_point_local_delete(self):
        rmdir(self.mount_point_local)

    def mount(self):
        """Mounts the sftp system if it's not already mounted."""
        if self.mounted:
            return

        self._mount_point_local_create()

        sshfs_options = " -o %s" % " -o ".join(self.system.mount_opts)

        cmd = ("{cmd_before_mount} &&"
               " /usr/bin/sshfs -o ssh_command='/usr/bin/ssh -p {port} -i {key}'"
               " {sshfs_options} {user}@{host}:{remote_path} {local_path}"
               " > /dev/null 2>&1")
        cmd = cmd.format(
            cmd_before_mount = self.system.cmd_before_mount,
            port = self.system.port,
            key = self.system.ssh_key,
            sshfs_options = sshfs_options,
            host = self.system.host,
            user = self.system.user,
            remote_path = self.mount_point_remote,
            local_path = self.mount_point_local,
        )

        shell_exec(cmd)

        # Clean up the directory tree if mounting failed
        if not self.mounted:
            self._mount_point_local_delete()

    def unmount(self):
        """Unmounts the sftp system if it's currently mounted."""
        if not self.mounted:
            return

        # Try to unmount properly.
        cmd = "/bin/fusermount -u %s > /dev/null 2>&1" % self.mount_point_local
        shell_exec(cmd)

        # The filesystem is probably still in use.
        # kill sshfs and it re-run this same command (which will work then).
        if self.mounted:
            self._kill()
            shell_exec(cmd)

        self._mount_point_local_delete()

    def _kill(self):
        pid = self.environment.get_pid_by_system_id(self.system.id)
        if pid is None:
            return
        kill_pid(pid, SystemControllerModel.SIGNAL_SIGTERM)

        from time import sleep
        sleep(SystemControllerModel.KILL_WAIT_TIME_SECONDS)

        pid = self.environment.get_pid_by_system_id(self.system.id)
        if pid is not None:
            kill_pid(pid, SystemControllerModel.SIGNAL_SIGKILL)
