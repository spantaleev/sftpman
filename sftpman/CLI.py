import sys
import json

from .SftpManager import SftpManager
from .SftpSystemController import SftpSystemController


class SftpCli(object):

	def __init__(self):
		self._manager = SftpManager()
	
	
	def command_help(self, *args, **kwargs):
		"""Displays this help menu."""
		
		print("Commands available:\n")
		
		for name in dir(self):
			if not name.startswith("command_"):
				continue
			
			name_clean = name[len("command_"):]
			print("%s:\n - %s\n" % (name_clean, getattr(self, name).__doc__))
				
	
	def command_ls(self, list_what):
		"""Lists the available/mounted/unmounted sftp systems.
		
		Usage: ./sftpman.py ls {what}
		Where {what} is one of: available, mounted, unmounted
		"""
		
		if list_what == "available":
			print(json.dumps(self._manager.get_available_ids()))
		elif list_what == "mounted":
			print(json.dumps(self._manager.get_mounted_ids()))
		elif list_what == "unmounted":
			print(json.dumps(self._manager.get_unmounted_ids()))
		else:
			raise Exception("Unknown list parameter!")
		
		
	def command_mount(self, system_id):
		"""Mounts the specified sftp system, unless it's already mounted.
		
		Usage: ./sftpman.py mount {id}
		"""
		
		controller = SftpSystemController.create_by_id(self._manager, system_id)
		controller.mount()
		
		
	def command_unmount(self, system_id):
		"""Unmounts the specified sftp system.
		
		Usage: ./sftpman.py unmount {id}
		"""
		
		controller = SftpSystemController.create_by_id(self._manager, system_id)
		controller.unmount()
		
		
	def command_mount_all(self):
		"""Mounts all available sftp file systems.
		
		Usage: ./sftpman.py mount_all
		"""
		
		for system_id in self._manager.get_unmounted_ids():
			controller = SftpSystemController.create_by_id(self._manager, system_id)
			controller.mount()


	def command_unmount_all(self):
		"""Unmounts all sftp file systems that are currently added.
		
		Usage: ./sftpman.py unmount_all
		"""
		
		for system_id in self._manager.get_mounted_ids():
			controller = SftpSystemController.create_by_id(self._manager, system_id)
			controller.unmount()

		
def start():
	command = sys.argv[1]
	args = sys.argv[2:]

	instance = SftpCli()
	callback = getattr(instance, "command_%s" % command, None)
	if callable(callback):
		callback(*args)
	else:
		instance.command_help()
