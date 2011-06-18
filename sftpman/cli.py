import sys
import getopt

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
            print("%s:\n - %s\n" % (name_clean, getattr(self, name).__doc__.strip()))

    def command_add(self, *args):
        """Adds (defines) a new sftp file system.
        Usage: sftpman add {options}
        Available {options}:
            --id={unique system identifier}
                You use this to recognize and manage this sftp system.
                It determines what the local mount point is.
                If `--id=example`, the filesystem will be mounted to: `/mnt/sshfs/example`
            --host={host to connect to}
            --port={port to connect to} [default: 22]
            --user={username to authenticate with} [default: current user]
            --mount_opts={comma separated list of sshfs options} [optional]
                Example: --mount_opts="follow_symlinks, workaround=rename, big_writes"
                `sshfs --help` tells you what sshfs options are available
            --mount_point={remote path to mount}
            --ssh_key={path to the ssh key to use for authentication}
            --cmd_before_mount={command to run before mounting} [default: /bin/true]
                Allows you to run a custom command every time this system is mounted.
        """
        def usage():
            print self.command_add.__doc__
            sys.exit(1)

        if len(args) == 0:
            usage()

        try:
            fields = [
                "id", "host", "port", "user",
                "mount_opts", "mount_point",
                "ssh_key", "cmd_before_mount",
            ]
            opts, _ = getopt.getopt(args, "", ["%s=" % s for s in fields])
        except getopt.GetoptError, e:
            sys.stderr.write('Eror: %s\n\n' % e)
            usage()

        system = SystemModel()
        for name, value in opts:
            name = name.lstrip('-')
            if not hasattr(system, name):
                continue
            if name == 'mount_opts':
                # Convert comma separated list to a python list
                value = [opt.strip() for opt in value.split(',')]
            setattr(system, name, value)

        is_valid, errors = system.validate()
        if not is_valid:
            sys.stderr.write('Invalid data found:\n')
            for field_name, msg in errors:
                sys.stderr.write(' - %s / %s\n' % (field_name, msg))
            sys.stderr.write('\n')
            usage()
            sys.exit(1)

        system.save(self.environment)
        print('Configuration created.')
        print('You can try mounting now: `sftpman mount %s`' % system.id)

    def command_rm(self, system_id, *system_ids):
        """Removes a system by id.
        Usage: sftpman rm {system_id}..
        For a list of system ids, see `sftpman ls available`.
        """
        # Intentionally reading the first system_id separately,
        # because it's required. The others are optional.
        # This ensures that we'll generate an error if someone tries to call
        # this without the required argument.
        system_ids = (system_id,) + system_ids
        has_failed = False
        for system_id in system_ids:
            try:
                system = SystemModel.create_by_id(system_id, self.environment)
                controller = SystemControllerModel(system, self.environment)
                controller.unmount()
                system.delete(self.environment)
            except SftpException, e:
                sys.stderr.write('Cannot remove %s: %s\n' % (system_id, str(e)))
                has_failed = True
        if has_failed:
            sys.exit(1)

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

    def command_mount(self, system_id, *system_ids):
        """Mounts the specified sftp system, unless it's already mounted.
        Usage: sftpman mount {id}..
        """
        system_ids = (system_id,) + system_ids
        has_failed = False
        for system_id in system_ids:
            try:
                system = SystemModel.create_by_id(system_id, self.environment)
                controller = SystemControllerModel(system, self.environment)
                controller.mount()
            except SftpException, e:
                sys.stderr.write('Cannot mount %s: %s' % (system_id, str(e)))
                has_failed = True
        if has_failed:
            sys.exit(1)

    def command_unmount(self, system_id, *system_ids):
        """Unmounts the specified sftp system.
        Usage: sftpman unmount {id}..
        """
        system_ids = (system_id,) + system_ids
        has_failed = False
        for system_id in system_ids:
            try:
                system = SystemModel.create_by_id(system_id, self.environment)
                controller = SystemControllerModel(system, self.environment)
                controller.unmount()
            except SftpException, e:
                sys.stderr.write('Cannot unmount %s: %s' % (system_id, str(e)))
                has_failed = True
        if has_failed:
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
                sys.stderr.write('Cannot mount %s: %s' % (system_id, str(e)))
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
                sys.stderr.write('Cannot unmount %s: %s' % (system_id, str(e)))
                has_failed = True
        sys.exit(0 if not has_failed else 1)


def start():
    try:
        command = sys.argv[1]
    except IndexError:
        command = 'help'
    if '--help' in sys.argv:
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
