class SftpException(Exception): pass


class SftpConfigException(SftpException): pass


class SftpMountException(SftpException):

    def __init__(self, mount_cmd, mount_cmd_output):
        self.mount_cmd = mount_cmd
        self.mount_cmd_output = mount_cmd_output
