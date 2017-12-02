"""
Create MP4
"""

from datetime import datetime
from os import path
from lib.cfg import load
from lib.main import iterate_path, VERSION
from lib.media import create_elements
from lib.prnt import params
import click

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
DEFAULT_CFG = r'{}\cfg\mp4.json'.format(path.dirname(path.realpath(__file__)))
STARTED = datetime.now()

@click.version_option(version=VERSION)
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('source')
@click.option('-cfg',
              type=click.File('r'),
              default=DEFAULT_CFG,
              help='Configuration file. (Default="{d}")'.format(d=DEFAULT_CFG))

def mp4(source, cfg):
    """
    Create MP4.
    """
    iterate_path(
        source,
        create_elements,
        cfg=load(cfg),
        title='CREATE MP4')
    ended = datetime.now()
    params([
        ['Started at', STARTED],
        ['Ended at', ended],
        ['Elapsed Time', ended - STARTED]
    ])

if __name__ == '__main__':
    mp4()
