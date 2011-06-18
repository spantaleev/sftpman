import os, errno
import subprocess

# Try to load the best json implementation,
# If json support is not available, we'll add
# an object that raises a RuntimeError when used
json = None
try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        try:
            # Google Appengine offers simplejson via django
            from django.utils import simplejson as json
        except ImportError:
            pass
if json is None:
    class _JSON(object):
        def __getattr__(self, name):
            raise RuntimeError('You need a JSON library to use sftpman!')
    json = _JSON()


def mkdir_p(path):
    """NOOP if the directory exists. If not, it creates the whole directory tree."""
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise


def rmdir(path):
    """Safe rmdir (non-recursive) which doesn't throw if the directory is not empty."""
    try:
        os.rmdir(path)
    except OSError as exc:
        print str(exc)


def shell_exec(command):
    """Executes the given shell command and returns its output."""
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]


def kill_pid(pid, signal):
    """Sends a signal to the process with the given id."""
    shell_exec("/bin/kill -%d %d" % (signal, pid))
