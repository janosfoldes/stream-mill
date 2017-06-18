"""
media module
"""

import datetime
import math
import os
import re
from subprocess import STDOUT
import sys
import lib.cfg
import lib.main
import lib.prnt

DEFAULT_HLS = {
    'output_dir': '',
    'output_single_file': True
}

DEFAULT_POSTER = {
    'height': 135,
    'index': '',
    'output': '{beforeext}-poster.jpg',
    'quality': 5,
    'stderr': None
}

DEFAULT_PREVIEW = {
    'height': 135,
    'output': '{beforeext}-preview.jpg',
    'quality': 5,
    'target_frames': 100
}

DEFAULT_VARIANT = {
    'height': 'source',
    'output': '{beforeext}.mp4',
    'width': 'source'
}

def create_elements(*args, **kwargs):
    """
    Creates media elements from 'src' according to 'cfg'.
    """

    #Initialize
    started = datetime.datetime.now()
    src = kwargs['src']
    cfg = kwargs['cfg']
    bext = os.path.splitext(src)[0]
    log = lib.main.Log('{}.log'.format(bext))
    stdout = sys.stdout
    sys.stdout = log
    lib.prnt.title(**kwargs)

    # Get media info
    info = lib.media.get_media_info(src, 'width', 'height', 'duration')

    # Print info
    lib.prnt.params([
        ['Version', lib.main.VERSION],
        ['Started at', started],
        ['Input', src],
        ['Duration', info['duration']],
        ['Resolution', '{w} x {h}'.format(w=info['width'], h=info['height'])]
    ])

    # Create MP4 variants
    mp4_list = lib.media.create_mp4_variants(src, cfg)
    # Create HLS
    lib.media.create_hls(mp4_list, cfg, source_beforeext=os.path.splitext(src)[0])
    # Create posters
    lib.media.create_posters(src, mp4_list, cfg, log_path=bext + '-posters.log')
    # Create preview image
    lib.media.create_preview(src, cfg)

    # Print summary
    ended = datetime.datetime.now()
    print
    lib.prnt.line(42)
    lib.prnt.params([
        ['Ended at', ended],
        ['Elapsed Time', ended - started]
    ])
    lib.prnt.line(42)

    # Close
    print
    sys.stdout = stdout
    log.close()


def create_hls(lst, *args, **kwargs):
    """
    Create HLS stream(s).
    """
    cfg = lib.cfg.get_settings('hls', DEFAULT_HLS, *args, **kwargs)
    if cfg:
        # Print info
        lib.prnt.h1('Create HLS')
        # Create HLS
        print lib.main.cmd(
            'mp4hls.bat --output-dir "{od}" {single} -f "{list}"'
            .format(
                od=lib.main.build_path(cfg['output_dir'], cfg['source_beforeext'], cfg),
                single=('--output-single-file') if cfg['output_single_file'] else '',
                list='" "'.join(lst)))
        #od = lib.main.build_path(cfg['output_dir'], cfg['source_beforeext'], cfg)
        #create_master_m3u8([od + r'\media-1\stream.m3u8'], '.\test.m3u8', True)


def create_master_m3u8(lst, output, fix=False):
    """
    Create master m3u8 from m3u8 files in 'lst'.
    """
    lib.prnt.h1('{action} master m3u8'.format(action=('Fix') if fix else 'Create'))

    # Initialize
    master = [1][0]

    # Process m3u8 files
    for m3u8_filename in lst:
        # Read m3u8 file
        m3u8_file = open(m3u8_filename, 'r')
        m3u8 = m3u8_file.read()
        m3u8_file.close()
        # Specify type (0 = stream, 1 = i-frame)
        sti = int('#EXT-X-I-FRAMES-ONLY' in m3u8)  # stream type index
        # Calculate max bandwith
        segments = re.findall(r'EXTINF:([\d\.]*)[^\d]*(\d*)@', m3u8, re.M|re.I)
        segment_bandwidths = [math.ceil(float(t2)/float(t1)*8) for (t1, t2) in segments]
        if fix:
            print 'LAST SEGMENT =', segment_bandwidths[-1]

        #print segment_bandwidths
        bandwidth = int(max(segment_bandwidths))
        #print 'MAX BANDWITH =', bandwidth

        total_bytes = sum(int(t2) for (t1, t2) in segments)
        total_duration = sum(float(t1) for (t1, t2) in segments)
        average_bandwidth = int(float(total_bytes * 8) / max(total_duration, 1))
        lib.prnt.params([
            ['size in bytes', total_bytes],
            ['duration in sec', total_duration],
            ['average bandwidth', average_bandwidth],
            ['max bandwidth', bandwidth],
            ['max/average', (float(bandwidth) / average_bandwidth ) * 100]
        ])

    # Write master m3u8 file



def create_mp4(src, template, *args):
    """
    Create an MP4 file.
    """
    lib.prnt.h1('Create MP4')

    # Get media width and height
    media_info = lib.media.get_media_info(src, 'width', 'height', 'duration')

    # Set variant parameters
    variant = DEFAULT_VARIANT.copy()
    if len(args) > 0 and isinstance(args[0], dict):
        variant.update(*args)
    if str(variant['height']).lower() == 'source':
        variant['height'] = media_info['height']
    if str(variant['width']).lower() == 'source':
        variant['width'] = media_info['width']
    variant['input'] = src
    variant['output'] = lib.main.build_path(variant['output'], src, variant)
    variant['scale'] = get_scale_param(media_info, variant)

    # Print info
    info = [
        ['Input', src],
        ['Output', variant['output']],
        ['Duration', media_info['duration']],
        ['Resolution', '{w} x {h}'.format(w=variant['width'], h=variant['height'])]
    ]
    if 'profile' in variant:
        info.append(['H.264 Profile', variant['profile']])
    if 'level' in variant:
        info.append(['H.264 Level', variant['level']])
    if 'crf' in variant:
        info.append(['Constant Rate Factor', variant['crf']])
    if 'maxrate' in variant:
        info.append(['VBV Maximum Rate', '{x} kbps'.format(x=variant['maxrate'])])
    if 'bufsize' in variant:
        info.append(['VBV Buffer Size', '{x} kbps'.format(x=variant['bufsize'])])
    if 'abr' in variant:
        info.append(['Audio Bitrate', '{x} kbps'.format(x=variant['abr'])])
    lib.prnt.params(info)

    # Execute FFmpeg
    report = "file='%s-mp4.log':level=40" %(os.path.splitext(variant['output'])[0])
    command = template.format(**variant)
    lib.media.ffmpeg(command, report, STDOUT)

    return variant['output']


def create_mp4_variants(src, cfg):
    """Create MP4 variants"""
    mp4_list = []
    media_info = lib.media.get_media_info(src, 'width', 'height')
    if 'variants' in cfg:
        for variant in cfg['variants']:
            if variant['height'] <= int(media_info['height']):
                mp4_list.append(
                    lib.media.create_mp4(src, cfg['template'], variant))
            else: break
    else:
        mp4_list.append(
            lib.media.create_mp4(src, cfg['template'], DEFAULT_VARIANT))
    return mp4_list


def create_poster(src, *args, **kwargs):
    """
    Create poster image from the first frame of the 'src' video file.
    """
    cfg = lib.cfg.get_settings('poster', DEFAULT_POSTER, *args, **kwargs)
    if cfg:
        lib.prnt.h1('Create poster')

        # Set parameters
        output = lib.main.build_path(cfg['output'], src, cfg)
        stderr = kwargs.get('stderr') or None

        # Print info
        lib.prnt.param('Input: ', src)
        lib.prnt.param('Output:', output)

        # Create poster
        ffmpeg('-loglevel verbose -y -i "{i}" -ss 00:00:00.000 -vframes 1 -q:v 5 "{o}"'
               .format(i=src, o=output),
               stderr=stderr)


def create_posters(src, lst, *args, **kwargs):
    """Create posters"""
    cfg = lib.cfg.get_settings('poster', DEFAULT_POSTER, *args, **kwargs)
    if cfg:
        posters_log = lib.main.Log(
            kwargs.get('log_path') or 'posters.log',
            True)
        for i in xrange(len(lst)):
            lib.media.create_poster(
                lst[i],
                args[0],
                stderr=posters_log.file,
                index=i+1,
                source_beforeext=os.path.splitext(src)[0])
            posters_log.sep()
        posters_log.close()


def create_preview(src, *args, **kwargs):
    """
    Create preview image.
    """
    cfg = lib.cfg.get_settings('preview', DEFAULT_PREVIEW, *args, **kwargs)
    if cfg:
        lib.prnt.h1('Create preview image')

        # Initialize
        src_frames = get_total_frames(src)
        step = max(int(src_frames / float(cfg['target_frames'])), 1)
        tile_cols = int(src_frames / step) + (src_frames % step and 1)
        bext = os.path.splitext(src)[0]
        png = bext + '-preview.png'
        jpg = lib.main.build_path(cfg['output'], src, cfg)

        #Print info
        lib.prnt.params([
            ['Input', src],
            ['Output', jpg],
            ['Input Frames', src_frames],
            ['Target Frames', cfg['target_frames']],
            ['Step', step],
            ['Tile Columns', tile_cols],
            ['Image Height', cfg['height']],
            ['JPEG Quality', cfg['quality']]
        ])

        preview_log = lib.main.Log(bext + '-preview.log', True)
        # Create preview PNG
        ffmpeg(
            r'-loglevel verbose -y -i "{i}" -frames 1 -vf "select=not(mod(n\,{s})),scale=-1:{h},tile={tc}x1" -vsync vfr "{o}"'
            .format(i=src, s=step, h=cfg['height'], tc=tile_cols, o=png),
            stderr=preview_log.file)
        preview_log.sep()
        # Create preview JPEG
        ffmpeg(
            '-loglevel verbose -y -i "{i}" -q:v {q} "{o}"'
            .format(i=png, o=jpg, q=cfg['quality']),
            stderr=preview_log.file)
        preview_log.close()


def ffmpeg(args, report=None, stderr=None):
    """
    Execute ffmpeg.exe with the given space separated 'args'.
    """
    lib.main.set_environ('FFREPORT', report)
    return lib.main.cmd('ffmpeg ' + args, stderr=stderr, echo=True)


def ffprobe(args, report=None, stderr=None):
    """
    Execute ffprobe.exe with the given space separated 'args'.
    """
    lib.main.set_environ('FFREPORT', report)
    return lib.main.cmd('ffprobe ' + args, stderr=stderr)


def get_media_info(src, *keys):
    """
    Get information about the given media file.
    """
    #lib.prnt.h1('Get media information')
    #lib.prnt.param('Input :', src)
    output = ffprobe(
        '-v error -show_entries stream={k} -of default=noprint_wrappers=1 -sexagesimal "{s}"'
        .format(k=','.join(keys), s=src))
    result = {}
    for key in keys:
        value = re.search(r'%s=([\d:.]*)' %(key), output).group(1)
        #lib.prnt.param('Output:', '%s = %s' %(key, value))
        result[key] = value
    return result


def get_scale_param(source, target):
    """Returns FFmpeg scale parameter"""
    return ('-vf scale=%s:%s' %(target['width'], target['height'])
            if source['width'] != target['width'] or source['height'] != target['height'] else '')


def get_total_frames(src):
    """
    Count the total frames of the 'src' media file.
    """
    output = ffmpeg('-i "{i}" -r 25 -f rawvideo -y NUL'
                    .format(i=src), stderr=STDOUT)
    return int(re.search(r'frame= *(\d*)', output).group(1))
    #output = ffprobe('-v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of default=nokey=1:noprint_wrappers=1 "{i}"'.format(i=src))
