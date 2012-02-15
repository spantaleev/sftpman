# -*- coding: utf-8 -*-

import os
import re
from .helper import json, shell_exec, mkdir_p, rmdir, kill_pid, which
from .exception import SftpConfigException, SftpMountException


class EnvironmentModel(object):
    """A configuration object that represents the environment
    with which we're now working.
    """

    def __init__(self):
        self.mount_path_base = '/mnt/sshfs/'
        cfg_home = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        self.config_path_base = "%s/" % os.path.join(cfg_home, 'sftpman')
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

        processes = shell_exec("ps ux | grep sshfs")
        for line in processes.split("\n"):
            match_object = regex.match(line)
            if match_object is None:
                continue
            return int(match_object.group(1))
        return None

    def get_available_ids(self):
        if not os.path.exists(self.config_path_mounts):
            return []
        cfg_files = shell_exec('ls %s' % self.config_path_mounts).strip().split('\n')
        return [file_name[0:-3] for file_name in cfg_files if file_name.endswith('.js')]

    def get_mounted_ids(self):
        # Looking for /mnt/sshfs/{id} in output that looks like this:
        # user@host:/remote/path on /mnt/sshfs/id type fuse.sshfs ...
        regex = re.compile(' %s(\w+) ' % self.mount_path_base)
        mounted = shell_exec('mount -l -t fuse.sshfs')
        return regex.findall(mounted)

    def get_unmounted_ids(self):
        ids_mounted = self.get_mounted_ids()
        return [id for id in self.get_available_ids() if id not in ids_mounted]

    def perform_preflight_check(self):
        """Performs checks to see if we have everything needed to mount
        sshfs filesystems.
        :return: two-tuple (boolean checks_pass, list failure messages)
        """
        failures = []
        if not os.access(self.mount_path_base, os.W_OK):
            msg = ("Mount path `{path}` doesn't exist or is not writable"
                   " by the current user.")
            failures.append(msg.format(
                path = self.mount_path_base
            ))
        if which('sshfs') is None:
            msg = ("SSHFS (http://fuse.sourceforge.net/sshfs.html)"
                   " does not seem to be installed.")
            failures.append(msg)

        return len(failures) == 0, failures


class SystemModel(object):
    """Represents a system (mount point) that sftpman manages."""

    PORT_RANGE_MIN = 0
    PORT_RANGE_MAX = 65535

    SSH_PORT_DEFAULT = 22

    AUTH_METHOD_PUBLIC_KEY = 'publickey'
    AUTH_METHOD_PASSWORD = 'password'

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.host = kwargs.get('host', None)
        self.port = kwargs.get('port', SystemModel.SSH_PORT_DEFAULT)
        self.user = kwargs.get('user', None)
        self.mount_opts = list(kwargs.get('mountOptions', []))
        self.mount_point = kwargs.get('mountPoint', None)
        self.auth_method = kwargs.get('authType', self.AUTH_METHOD_PUBLIC_KEY)
        self.ssh_key = kwargs.get('sshKey', None)
        self.cmd_before_mount = kwargs.get('beforeMount', 'true')

    def _set_port(self, value):
        self._port = int(value)

    port = property(lambda self: self._port, _set_port)

    def _set_ssh_key(self, value):
        if value is not None:
            value = os.path.expanduser(value)
        self._ssh_key = value

    ssh_key = property(lambda self: self._ssh_key, _set_ssh_key)

    def validate(self):
        def is_alphanumeric(value):
            if value is None:
                return False
            # Well, not really alphanumeric, but close enough to call it that
            return re.compile('^[a-zA-Z0-9\.\-]+$').match(value) is not None

        def is_valid_path(value):
            if value is None:
                return False
            return re.compile('^/(([a-zA-Z0-9\.\-_]+)/?)*?$').match(value) is not None

        errors = []
        if not is_alphanumeric(self.id):
            errors.append(('id', 'IDs can only contain letters, digits, dot and dash.'))
        if not is_alphanumeric(self.host):
            errors.append(('host', 'Hosts can only contain letters, digits, dot and dash.'))
        if not is_valid_path(self.mount_point):
            errors.append(('mount_point', 'Invalid remote mount point.'))
        if self.auth_method not in (self.AUTH_METHOD_PUBLIC_KEY, self.AUTH_METHOD_PASSWORD):
            errors.append(('auth_method', 'Unknown auth type.'))
        else:
            if self.auth_method == self.AUTH_METHOD_PUBLIC_KEY:
                if not os.path.exists(self.ssh_key):
                    errors.append(('ssh_key', 'Invalid ssh key path.'))
        if not is_alphanumeric(self.user):
            errors.append(('user', 'Usernames can only contain letters and digits.'))
        if not(self.PORT_RANGE_MIN < self.port <= self.PORT_RANGE_MAX):
            msg = 'Ports need to be numbers between %d and %d.' % (
                self.PORT_RANGE_MIN,
                self.PORT_RANGE_MAX,
            )
            errors.append(('port', msg))
        if not isinstance(self.mount_opts, list):
            errors.append(('mount_opts', 'Bad options received.'))
        if not isinstance(self.cmd_before_mount, str) or \
           self.cmd_before_mount == '':
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
        out['authType'] = self.auth_method
        out['sshKey'] = self.ssh_key
        return json.dumps(out)

    def save(self, environment):
        path = environment.get_system_config_path(self.id)
        mkdir_p(os.path.dirname(path))
        with open(path, 'w') as f:
            f.write(self.export())

    def delete(self, environment):
        path = environment.get_system_config_path(self.id)
        os.unlink(path)

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
        except (ValueError, IOError) as e:
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

    #: Time to wait for sshfs (ssh) to establish a connection
    SSH_CONNECT_TIMEOUT = 8

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
        shell_exec('fusermount -u %s' % self.mount_point_local)

        # Ensure the directory path exists
        mkdir_p(self.mount_point_local)

    def _mount_point_local_delete(self):
        rmdir(self.mount_point_local)

    def mount(self):
        """Mounts the sftp system if it's not already mounted."""
        if self.mounted:
            return

        self._mount_point_local_create()

        if len(self.system.mount_opts) == 0:
            sshfs_opts = ""
        else:
            sshfs_opts = " -o %s" % " -o ".join(self.system.mount_opts)

        if self.system.auth_method == self.system.AUTH_METHOD_PUBLIC_KEY:
            ssh_opts = '-o PreferredAuthentications=publickey -i %s' % self.system.ssh_key
        else:
            ssh_opts = '-o PreferredAuthentications=password'

        cmd = ("{cmd_before_mount} &&"
               " sshfs -o ssh_command="
               "'ssh -o ConnectTimeout={timeout} -p {port} {ssh_opts}'"
               " {sshfs_opts} {user}@{host}:{remote_path} {local_path}")
        cmd = cmd.format(
            cmd_before_mount = self.system.cmd_before_mount,
            timeout = self.SSH_CONNECT_TIMEOUT,
            port = self.system.port,
            ssh_opts = ssh_opts,
            sshfs_opts = sshfs_opts,
            host = self.system.host,
            user = self.system.user,
            remote_path = self.mount_point_remote,
            local_path = self.mount_point_local,
        )

        output = shell_exec(cmd).strip()

        if not self.mounted:
            # Clean up the directory tree
            self._mount_point_local_delete()
            if output == '':
                output = 'Mounting failed for a reason unknown to sftpman.'
            raise SftpMountException(cmd, output)

    def unmount(self):
        """Unmounts the sftp system if it's currently mounted."""
        if not self.mounted:
            return

        # Try to unmount properly.
        cmd = 'fusermount -u %s' % self.mount_point_local
        shell_exec(cmd)

        # The filesystem is probably still in use.
        # kill sshfs and re-run this same command (which will work then).
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
