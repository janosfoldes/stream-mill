"""
M3U8 PROCESSOR
"""

import sys
from datetime import datetime, timedelta
from os import getcwd, path, sep
from lib.main import VERSION
from lib.media import DEFAULT_M3U8, process_m3u8_file
import click
import glob2
import lib.cfg
import lib.prnt

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
DEFAULT_CFG = r'{}\cfg\m3u8.json'.format(path.dirname(path.realpath(__file__)))
STARTED = datetime.now()

@click.version_option(version=VERSION)
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('source')
@click.option('-cfg',
              type=click.File('r'),
              default=DEFAULT_CFG,
              help='Configuration file. (Default="{d}")'.format(d=DEFAULT_CFG))

def m3u8(source, cfg):
    # Initialize
    log_path = 'm3u8-{}.log'.format(datetime.strftime(STARTED, '%Y%m%d-%H%M%S'))
    log = lib.main.Log(log_path)
    stdout = sys.stdout
    sys.stdout = log

   # Print info
    lib.prnt.title(title='STREAM MILL -', src='M3U8 Processor')
    lib.prnt.params([
        ['Version', VERSION],
        ['Source', source],
        ['Log', getcwd() + sep + log_path]
    ])

    # Print config
    cfg = lib.cfg.get_settings('m3u8', DEFAULT_M3U8, lib.cfg.load(cfg))
    lib.prnt.h1('Configuration')
    lib.prnt.param('Add CLOSED_CAPTION=NONE:', cfg['add_closed_captions_none'])
    lib.prnt.param('Remove comments:', cfg['remove_comments'])

    # Process files
    lib.prnt.h1('Processed files')
    lst = glob2.glob(source)
    total = len(lst)
    zerofill = len(str(total))
    modified_total = 0
    index = 0
    for src in lst:
        index += 1
        modified = process_m3u8_file(src, cfg)
        modified_total += modified
        modified_text = lib.prnt.MAIN_COLOR + ' [Modified]' if modified else ''
        print lib.prnt.LABEL_COLOR + '  [' + str(total) + '/' + str(index).zfill(zerofill) + '] ' \
            + lib.prnt.DEFAULT_COLOR + src \
            + modified_text \
            + lib.prnt.DEFAULT_COLOR

    # Print summary
    ENDED = datetime.now()
    print
    lib.prnt.line(42)
    lib.prnt.params([
        ['Processed', total],
        ['Modified', modified_total],
        ['Started at', STARTED],
        ['Ended at', ENDED],
        ['Elapsed Time', ENDED - STARTED]
    ])
    lib.prnt.line(42)

    # Close
    sys.stdout = stdout
    log.close()


if __name__ == '__main__':
    m3u8()
