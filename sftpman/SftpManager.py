"""
This file contains the SftpManager class, which manages all the sftp systems,
by spawning the appropriate controllers and controlling their actions.

It's the only class that can deals with the global sftp systems state.
"""

import re
import os

from .helper import mkdir_p, shell_exec

class SftpManager(object):
	
	def __init__(self):
		self._mount_base = "/mnt/sshfs/"
		self._config_base = os.path.expanduser("~/.config/sftpman/")

		mkdir_p(self.config_path_mounts)


	@property
	def config_path_base(self):
		return self._config_base


	@property
	def config_path_mounts(self):
		return self._config_base + "mounts/"


	@property
	def mount_path_base(self):
		return self._mount_base
	
	
	def is_mounted(self, system_id):
		return system_id in self.get_mounted_ids()
	
	
	def get_pid_by_system_id(self, system_id):
		processes = shell_exec("/bin/ps ux | /bin/grep '/usr/bin/sshfs'")
		
		# Looking for `username {PID} blah blah /mnt/sshfs/{id}`
		regex = re.compile(r"(?:\w+)\s([0-9]+)(?:.+?)%s(?:\w+)" % re.escape(self._mount_base))
		
		mount_point = "%s%s" % (self._mount_base, system_id)
		
		ids = []
		for line in processes.split("\n"):
			if mount_point not in line:
				continue

			match_object = regex.search(line)
			if match_object is None:
				continue
			
			return int(match_object.group(1))

		return None
	

	def get_available_ids(self):
		cfg_files = shell_exec("/bin/ls %s" % self.config_path_mounts).strip().split("\n")
		return [file_name[0:-3] for file_name in cfg_files if file_name.endswith(".js")]
	
	
	def get_mounted_ids(self):
		processes = shell_exec("/bin/ps ux | /bin/grep sshfs")

		# Looking for /mnt/sshfs/{id}
		regex = re.compile(r"(%s)(\w+)" % re.escape(self._mount_base))
		
		ids = []
		for line in processes.split("\n"):
			if self._mount_base not in line:
				continue
			
			match_object = re.search(regex, line)
			if (match_object is None):
				continue
			
			ids.append(match_object.group(2))

		return ids
	
	
	def get_unmounted_ids(self):
		ids_mounted = self.get_mounted_ids()
		return [id for id in self.get_available_ids() if id not in ids_mounted]

