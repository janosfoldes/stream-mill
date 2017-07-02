"""
main module
"""

import glob2
import os
import re
import shlex
import subprocess
import sys
import colorama

VERSION = '0.3.0'

colorama.init()


def ansi_escape(text):
    """Removes ANSI escape codes from 'text'."""
    reaesc = re.compile(r'\x1b[^m]*m')
    return reaesc.sub('', text)


def build_path(pattern, path, *values):
    """Build path"""
    dn = os.path.dirname(path)
    defaults = {
        'beforeext':os.path.splitext(path)[0],
        'dirname': ('') if dn == '' else dn + '\\',
        'filename':os.path.splitext(os.path.basename(path))[0]
    }
    merged = defaults.copy()
    if values:
        merged.update(*values)
    return os.path.normpath(pattern.format(**merged))

#def cmd(command, stderr=None):
#    """Execute command."""
#    return subprocess.Popen(
#        shlex.split(command),
#        stdout=subprocess.PIPE,
#        stderr=stderr,
#        universal_newlines=True
#    ).communicate()[0]


def cmd(command, stderr=None, echo=False):
    """Execute command."""
    iswrite = False
    cols = 120
    output = ''
    #print command
    #print 'stderr =', stderr
    #print 'echo =', echo
    p = subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=stderr,
        universal_newlines=True
    )
    #print 'subprocess stderr', p.stderr
    while True:
        line = p.stdout.readline()
        output += line
        if not line:
            break
        if echo:
            #cols = terminalsize.get_terminal_size()[0] - 2
            #sys.stdout.write(Back.BLACK + Fore.LIGHTGREEN_EX + '\r  ' + line[:cols][:-1].ljust(cols-1))
            sys.stdout.write('\033[2K\r  {c}{t}'.format(c=colorama.Fore.GREEN, t=line[:cols][:-1]))
            iswrite = True
    if echo and iswrite:
        sys.stdout.write('\033[0K\n')
    return output


def iterate_path(path, callback, *args, **kwargs):
    """Iterate through the 'path' and call callback function on every item."""
    lst = glob2.glob(path)
    total = len(lst)
    index = 0
    for src in lst:
        index += 1
        callback(*args, src=src, total=total, index=index, **kwargs)


def set_environ(key, value=None):
    """
    Set 'key' environment variable to the given 'value'.
    If 'value' is None, delete 'key' environment variable (if it exists).

    Args:
        key:   The name of the environment variable.
        value: The value of the environment variable.
    """
    if value is None:
        if os.environ.has_key(key):
            del os.environ[key]
    else:
        os.environ[key] = value


class Log(object):
    """
    Log to console and file
    """
    separator = '\n' + '-'*160 + '\n\n'

    def __init__(self, filename, silent=False):
        self.file = open(filename, 'w')
        self.console = sys.stdout
        self.silent = silent

    def close(self):
        """close"""
        self.file.close()

    def sep(self):
        """separator"""
        if self.silent is False:
            self.console.write(Log.separator)
        self.file.flush()
        self.file.write(Log.separator)
        self.file.flush()

    def write(self, message):
        """write"""
        if self.silent is False:
            self.console.write(message)
        #if not message.startswith('\033[2K'):
        if not re.match('^\033\[\dK', message):
            self.file.write(ansi_escape(message))
