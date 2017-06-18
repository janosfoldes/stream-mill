"""
cfg module
"""

import json
import os
import sys


def get_settings(key, defaults, *args, **kwargs):
    """Takes config object from args[0], and returns settings specified by 'key'."""
    if len(args) == 0 or key not in args[0] or args[0][key] is False:
        return False
    cfg = defaults.copy()
    for k,v in kwargs.iteritems():
        cfg[k] = v
    if args[0][key] is not True:
        cfg.update(args[0][key])
    return cfg


def isset(cfg, key):
    """Returns True when 'key' is set in 'cfg', else returns False."""
    return ((key in cfg) and (cfg[key] is True)) or isinstance(cfg[key], dict)


def load(cfg_file):
    """Load config file"""
    cfg = json.load(cfg_file)
    template = open(
        r'{dn}\templates\{t}.txt'.format(
            dn=os.path.dirname(
                os.path.realpath(
                    sys.argv[0])),
            t=cfg['template']),
        'r')
    cfg['template'] = template.read()
    template.close()
    return cfg
