"""
prnt module
"""

from colorama import Fore, init, Style
from lib.main import ansi_escape

init() #Initialize colorama => It needs to colors in Windows terminal!

DEFAULT_COLOR = Style.RESET_ALL
MAIN_COLOR = Fore.YELLOW
LABEL_COLOR = Fore.CYAN


def heading1(text):
    """Print heading 1 text"""
    print '\n' + MAIN_COLOR + str(text) + DEFAULT_COLOR


def line(length):
    """Print line"""
    print MAIN_COLOR + '-' * length + DEFAULT_COLOR


def param(name, value):
    """Print parameter name and value"""
    print '  ' + LABEL_COLOR + name + DEFAULT_COLOR + ' ' + str(value)


def params(param_list):
    """Print parameter list"""
    # length of the longest label + 2
    length = len(max(param_list, key=lambda item: len(item[0]))[0]) + 2
    for par in param_list:
        print '  ' + LABEL_COLOR + (par[0] + ':').ljust(length) + DEFAULT_COLOR + str(par[1])


def title(**kwargs):
    """Print title ribbon"""
    text = ''
    if 'total' in kwargs:
        text += LABEL_COLOR + str(kwargs['total']) + '/'
    if 'index' in kwargs:
        text += LABEL_COLOR + str(kwargs['index']) + ' '
    if 'title' in kwargs:
        text += MAIN_COLOR + kwargs['title']
    if 'src' in kwargs:
        text += LABEL_COLOR + ' ' + kwargs['src'] + MAIN_COLOR
    horizontal_line = '-' * (len(ansi_escape(text)))
    print MAIN_COLOR + horizontal_line
    print text
    print horizontal_line + DEFAULT_COLOR
