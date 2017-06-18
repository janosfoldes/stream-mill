"""
prnt module
"""

from colorama import Fore, init, Style
from lib.main import ansi_escape

init() #Initialize colorama => It needs to colors in Windows terminal!

MAIN_COLOR = Fore.YELLOW
LABEL_COLOR = Fore.CYAN


def h1(text):
    """Print heading 1 text"""
    print '\n' + MAIN_COLOR + str(text) + Style.RESET_ALL


def line(length):
    """Print line"""
    print MAIN_COLOR + '-' * length + Style.RESET_ALL


def param(name, value):
    """Print parameter name and value"""
    print '  ' + LABEL_COLOR + name + Style.RESET_ALL + ' ' + str(value)


def params(param_list):
    """Print parameter list"""
    m = len(max(param_list, key=lambda item:len(item[0]))[0])+2 #length of the longest label + 2
    for p in param_list:
        print '  ' + LABEL_COLOR + (p[0] + ':').ljust(m) + Style.RESET_ALL + str(p[1])


def title(**kwargs):
    """Print title ribbon"""
    text = ''
    if 'total' in kwargs: text += LABEL_COLOR + str(kwargs['total']) + '/'
    if 'index' in kwargs: text += LABEL_COLOR + str(kwargs['index'])
    if 'title' in kwargs: text += MAIN_COLOR + ' ' + kwargs['title']
    if 'src' in kwargs: text += LABEL_COLOR + ' ' + kwargs['src'] + MAIN_COLOR
    line = '-' * (len(ansi_escape(text)))
    print MAIN_COLOR + line
    print text
    print line + Style.RESET_ALL
