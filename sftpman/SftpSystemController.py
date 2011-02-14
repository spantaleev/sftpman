"""
This file contains the SftpSystemController class, an instance of which controls a single sftp system.

It can mount/unmount an sftp system or manage its settings, but it doesn't know much about
the global state (mounted sftp systems, their PIDs, etc.)

This class uses the SftpManager to access information from the outside world.

"""

import json
import os
from time import sleep

from .helper import rmdir, shell_exec, kill_pid, mkdir_p
from .exception import SftpConfigException


FIELD_ID = "id"
FIELD_HOST = "host"
FIELD_PORT = "port"
FIELD_USER = "user"
FIELD_SSH_KEY = "sshKey"
FIELD_MOUNT_POINT = "mountPoint"
FIELD_MOUNT_OPTIONS = "mountOptions"
FIELD_COMMAND_BEFORE_MOUNT = "beforeMount"


def get_config_fields(is_added):
	lst = []
	lst.append({"id": FIELD_ID, "type": "textbox", "title": "Id/Name", "defaultValue": "", "isDisabled": is_added})
	lst.append({"id": FIELD_HOST, "type": "textbox", "title": "Host", "defaultValue": ""})
	lst.append({"id": FIELD_PORT, "type": "textbox", "title": "Port", "defaultValue": 22})
	lst.append({"id": FIELD_USER, "type": "textbox", "title": "User", "defaultValue": ""})
	lst.append({"id": FIELD_SSH_KEY, "type": "filepath", "title": "SSH Key", "defaultValue": ""})
	lst.append({"id": FIELD_MOUNT_POINT, "type": "textbox", "title": "Remote mount point", "defaultValue": "/var/www/vhosts/"})
	lst.append({"id": FIELD_MOUNT_OPTIONS, "type": "options", "title": "Options", "defaultValue": ["follow_symlinks", "workaround=rename", "big_writes"]})
	lst.append({"id": FIELD_COMMAND_BEFORE_MOUNT, "type": "textbox", "title": "Run before mount", "defaultValue": "/bin/true"})
	
	return lst


class SftpSystemController(object):
	
	def __init__(self, sftp_manager, system_id):
		self._manager = sftp_manager
		self._id = system_id
		self._config = {}
		self._is_added = False
	
	
	@property
	def id(self):
		return self._id
	
	
	@property
	def is_added(self):
		return self._is_added
	
	
	@property
	def config_path(self):
		return "%s%s.js" % (self._manager.config_path_mounts, self._id)
	
	
	def config_load(self):
		"""Loads the configuration for the given system.
		
		It throws an SftpConfigException if the file cannot be read or doesn't exist.
		
		"""
		
		try:
			self._config = json.loads(open(self.config_path).read())
			self._is_added = True
		except Exception as e:
			raise SftpConfigException(repr(e))
	
	
	def config_write(self):
		"""Writes the sftp system's configuration to the file system."""
		
		open(self.config_path, "w").write(json.dumps(self._config))
		self._is_added = True
	
	
	def config_delete(self):
		"""Deletes the sftp system's configuration from the file system."""
		
		os.unlink(self.config_path)
	
	
	@staticmethod
	def create_by_id(manager, system_id):
		obj = SftpSystemController(manager, system_id)
		obj.config_load()
		
		return obj
	
	
	@property
	def host(self):
		return self._config[FIELD_HOST]
		
	@property
	def port(self):
		return self._config[FIELD_PORT]
		
	@property
	def username(self):
		return self._config[FIELD_USER]
	
	@property
	def mount_point_remote(self):
		return self._config[FIELD_MOUNT_POINT]
	
	
	@property
	def mount_point_local(self):
		return "%s%s" % (self._manager.mount_path_base, self._id)
	
	
	def mount_point_local_create(self):
		"""Ensures the mount location exists, so we can start using it."""
		
		# Ensure nothing's mounted there right now..
		shell_exec("/bin/fusermount -u %s 2>&1" % self.mount_point_local)
		
		# Ensure the directory path exists
		mkdir_p(self.mount_point_local)
	
	
	def mount_point_local_delete(self):
		if self._is_added:
			rmdir(self.mount_point_local)
	
	
	@property
	def mount_options_list(self):
		options = self._config[FIELD_MOUNT_OPTIONS]
		
		options.append('ssh_command="/usr/bin/ssh -p {PORT} -i {KEY}"')
		
		return options
	
	
	@property
	def ssh_key_path(self):
		return self._config[FIELD_SSH_KEY]
	
	
	@property
	def command_before_mount(self):
		return self._config[FIELD_COMMAND_BEFORE_MOUNT]
	
	
	def config_get(self, key, default_value=None):
		if key == FIELD_ID:
			return self.id
		
		return self._config[key] if key in self._config else default_value
	
	
	def config_set(self, key, value):
		if key == FIELD_ID and not self._is_added:
			self._id = value
			return
		
		self._config[key] = value
	

	def _kill(self):
		pid = self._manager.get_pid_by_system_id(self._id)
		if pid is None:
			return
		kill_pid(pid, 15)

		sleep(2)

		pid = self._manager.get_pid_by_system_id(self._id)
		if pid is not None:
			kill_pid(pid, 9)
	
	
	@property
	def is_mounted(self):
		return self._manager.is_mounted(self._id)
		
	
	def mount(self):
		"""Mounts the sftp system if it's not already mounted."""
		
		if self.is_mounted:
			return
		
		self.mount_point_local_create()
		
		options = " -o %s" % " -o ".join(self.mount_options_list)
			
		cmd = "{BEFORE_MOUNT} && /usr/bin/sshfs %s {USER}@{HOST}:{REMOTE_DIR} {LOCAL_DIR} > /dev/null 2>&1" % options
				
		replacements = {}
		replacements["{BEFORE_MOUNT}"] = self.command_before_mount
		replacements["{HOST}"] = self.host
		replacements["{PORT}"] = str(self.port)
		replacements["{USER}"] = self.username
		replacements["{KEY}"] = self.ssh_key_path
		replacements["{REMOTE_DIR}"] = self.mount_point_remote
		replacements["{LOCAL_DIR}"] = self.mount_point_local
		
		for k, v in replacements.items():
			cmd = cmd.replace(k, v)
		
		shell_exec(cmd)
		
		# Clean up the directory tree if mounting failed
		if not self.is_mounted:
			self.mount_point_local_delete()
	
	
	def unmount(self):
		"""Unmounts the sftp system if it's currently mounted."""
		
		if not self.is_mounted:
			return
	
		cmd = "/bin/fusermount -u %s > /dev/null 2>&1" % self.mount_point_local
		shell_exec(cmd)
		
		if self.is_mounted:
			self._kill()
			shell_exec(cmd)
 		
		self.mount_point_local_delete()

