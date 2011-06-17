import sys

from exception import SftpException
from model import EnvironmentModel, SystemModel, SystemControllerModel


class SftpCli(object):

    def __init__(self):
        self.environment = EnvironmentModel()

    def command_help(self, *args, **kwargs):
        """Displays this help menu."""
        print("Commands available:\n")
        for name in dir(self):
            if not name.startswith("command_"):
                continue
            name_clean = name[len("command_"):]
            print("%s:\n - %s\n" % (name_clean, getattr(self, name).__doc__))

    def command_preflight_check(self):
        """Detects whether we have everything needed to mount sshfs filesystems.
        """
        checks_pass, failures = self.environment.perform_preflight_check()
        if checks_pass:
            print('All checks pass.')
        else:
            sys.stderr.write('Problems encountered:\n')
            for msg in failures:
                sys.stderr.write(' - %s\n' % msg)
            sys.exit(1)

    def command_ls(self, list_what):
        """Lists the available/mounted/unmounted sftp systems.

        Usage: sftpman ls {what}
        Where {what} is one of: available, mounted, unmounted
        """
        if list_what in ('available', 'mounted', 'unmounted'):
            callback = getattr(self.environment, 'get_%s_ids' % list_what)
            lst = callback()
        else:
            lst = []
        if len(lst) != 0:
            print("\n".join(lst))

    def command_mount(self, system_id):
        """Mounts the specified sftp system, unless it's already mounted.

        Usage: sftpman mount {id}
        """
        try:
            system = SystemModel.create_by_id(system_id, self.environment)
            controller = SystemControllerModel(system, self.environment)
            controller.mount()
        except SftpException, e:
            sys.stderr.write('Cannot mount: %s' % str(e))
            sys.exit(1)

    def command_unmount(self, system_id):
        """Unmounts the specified sftp system.

        Usage: sftpman unmount {id}
        """
        try:
            system = SystemModel.create_by_id(system_id, self.environment)
            controller = SystemControllerModel(system, self.environment)
            controller.unmount()
        except SftpException, e:
            sys.stderr.write('Cannot unmount: %s' % str(e))
            sys.exit(1)

    def command_mount_all(self):
        """Mounts all sftp file systems known to sftpman.

        Usage: sftpman mount_all
        """
        has_failed = False
        for system_id in self.environment.get_unmounted_ids():
            try:
                system = SystemModel.create_by_id(system_id, self.environment)
                controller = SystemControllerModel(system, self.environment)
                controller.mount()
            except SftpException, e:
                sys.stderr.write('Cannot mount: %s' % str(e))
                has_failed = True
        sys.exit(0 if not has_failed else 1)

    def command_unmount_all(self):
        """Unmounts all sftp file systems known to sftpman.

        Usage: sftpman unmount_all
        """
        has_failed = False
        for system_id in self.environment.get_mounted_ids():
            try:
                system = SystemModel.create_by_id(system_id, self.environment)
                controller = SystemControllerModel(system, self.environment)
                controller.unmount()
            except SftpException, e:
                sys.stderr.write('Cannot unmount: %s' % str(e))
                has_failed = True
        sys.exit(0 if not has_failed else 1)


def start():
    try:
        command = sys.argv[1]
    except IndexError:
        command = 'help'
    args = sys.argv[2:]

    instance = SftpCli()
    callback = getattr(instance, "command_%s" % command, None)
    if callable(callback):
        try:
            callback(*args)
        except TypeError, e:
            sys.stderr.write('Bad call for %s: %s' % (command, str(e)))
    else:
        instance.command_help()
