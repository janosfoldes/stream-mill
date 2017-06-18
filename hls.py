"""
Create HLS streams.
"""

from datetime import datetime, timedelta
from os import path
from lib.cfg import load
from lib.main import iterate_path, VERSION
from lib.media import create_elements
from lib.prnt import params
import click

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
DEFAULT_CFG = r'{}\cfg\hls.json'.format(path.dirname(path.realpath(__file__)))
STARTED = datetime.now()

@click.version_option(VERSION)
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('source')
@click.option('-cfg',
              type=click.File('r'),
              default=DEFAULT_CFG,
              help='Configuration file. (Default="{d}")'.format(d=DEFAULT_CFG))

def hls(source, cfg):
    iterate_path(
        source,
        create_elements,
        cfg=load(cfg),
        title='CREATE HLS')
    ENDED = datetime.now()
    params([
        ['Started at', STARTED],
        ['Ended at', ENDED],
        ['Elapsed Time', ENDED - STARTED]
    ])

if __name__ == '__main__':
    hls()
