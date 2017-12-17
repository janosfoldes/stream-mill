"""
media module
"""

import datetime
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

DEFAULT_M3U8 = {
    'add_closed_captions_none': False,
    'remove_comments': False
}

DEFAULT_POSTER = {
    'index': '',
    'output': '{beforeext}-poster.jpg',
    'position': '00:00:00.000000',
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
    'crf': 23,
    'output': '{beforeext}.mp4'
}

def create_elements(**kwargs):
    """
    Creates media elements from 'src' according to 'cfg'.
    """

    # Initialize
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
    master_m3u8 = lib.media.create_hls(mp4_list, cfg, source_beforeext=os.path.splitext(src)[0])
    # Process M3U8
    lib.media.process_m3u8(master_m3u8, cfg)
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
        lib.prnt.heading1('Create HLS')
        # Create HLS
        output_dir = lib.main.build_path(cfg['output_dir'], cfg['source_beforeext'], cfg)
        print lib.main.cmd(
            'mp4hls.bat --output-dir "{od}" {single} -f "{list}"'
            .format(
                od=output_dir,
                single=('--output-single-file') if cfg['output_single_file'] else '',
                list='" "'.join(lst)))
        return os.path.join(output_dir, 'master.m3u8')


def create_mp4(src, template, *args):
    """
    Create an MP4 file.
    """
    lib.prnt.heading1('Create MP4')

    # Get media width and height
    media_info = lib.media.get_media_info(src, 'width', 'height', 'duration')

    # Set variant parameters
    variant = DEFAULT_VARIANT.copy()
    if args and isinstance(args[0], dict):
        variant.update(*args)
    if 'height' not in variant:
        variant['height'] = media_info['height']
    if 'width' not in variant:
        variant['width'] = media_info['width']
    variant['input'] = src
    variant['output'] = lib.main.fix_existing_path(
        lib.main.build_path(variant['output'], src, variant))
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
    if 'template' in cfg:
        media_info = lib.media.get_media_info(src, 'height')
        if 'variants' in cfg and isinstance(cfg['variants'], list):
            for variant in cfg['variants']:
                height = (variant['height'] if 'height' in variant
                          and isinstance(variant['height'], (int, long))
                          else int(media_info['height']))
                if height <= int(media_info['height']):
                    mp4_list.append(
                        lib.media.create_mp4(src, cfg['template'], variant))
        elif ('variants' in cfg and cfg['variants']) or ('variants' not in cfg):
            mp4_list.append(
                lib.media.create_mp4(src, cfg['template'], DEFAULT_VARIANT))
    elif 'variants' in cfg and cfg['variants']:
        print '{c}\nNo template is specified!'.format(c=lib.prnt.ERROR_COLOR)
    return mp4_list


def create_poster(src, *args, **kwargs):
    """
    Create poster image from the first frame of the 'src' video file.
    """
    cfg = lib.cfg.get_settings('poster', DEFAULT_POSTER, *args, **kwargs)
    if cfg:
        lib.prnt.heading1('Create poster')

        # Set parameters
        output = lib.main.build_path(cfg['output'], src, cfg)
        stderr = kwargs.get('stderr') or None
        ## Set position
        media_info = lib.media.get_media_info(src, 'duration')
        duration = datetime.datetime.strptime(media_info['duration'], '%H:%M:%S.%f')
        position = datetime.datetime.strptime(cfg['position'], '%H:%M:%S.%f')
        new_position_text = ''
        if duration < position:
            position = max(datetime.datetime.strptime('0', '%f'),
                           duration - datetime.timedelta(seconds=1))
            new_position_text = ' {c} Using {p}!'.format(c=lib.prnt.WARNING_COLOR,
                                                         p=position.time())

        # Print info
        lib.prnt.params([
            ['Input', src],
            ['Output', output],
            ['Position', cfg['position'] + new_position_text],
            ['Quality', cfg['quality']]
        ])

        # Create poster
        ffmpeg('-loglevel verbose -y -i "{i}" -ss {p} -vframes 1 -q:v {q} "{o}"'
               .format(i=src, o=output, p=position.time(), q=cfg['quality']),
               stderr=stderr)


def create_posters(src, lst, *args, **kwargs):
    """Create posters"""
    cfg = lib.cfg.get_settings('poster', DEFAULT_POSTER, *args, **kwargs)
    if cfg:
        posters_log = lib.main.Log(
            kwargs.get('log_path') or 'posters.log',
            True)
        if not lst:
            lst.append(src)
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
        lib.prnt.heading1('Create preview image')

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
            ('-loglevel verbose -y -i "{i}" -frames 1 '
             '-vf "select=\'not(mod(n,{s}))\',scale=-1:{h},tile={tc}x1" -vsync vfr "{o}"')
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
    #lib.prnt.heading1('Get media information')
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
    # output = ffprobe(
    #     ('-v error -count_frames'
    #      '-select_streams v:0'
    #      '-show_entries stream=nb_read_frames'
    #      '-of default=nokey=1:noprint_wrappers=1 "{i}"').format(i=src))
    return int(re.search(r'frame= *(\d*)', output).group(1))


def process_m3u8(filename, *args, **kwargs):
    """
    Process m3u8
    """
    if filename:
        cfg = lib.cfg.get_settings('m3u8', DEFAULT_M3U8, *args, **kwargs)
        if cfg:
            # Print info
            lib.prnt.heading1('Process M3U8')
            lib.prnt.param('Filename:', filename)
            lib.prnt.param('Add CLOSED-CAPTION=NONE:', cfg['add_closed_captions_none'])
            lib.prnt.param('Remove comments:', cfg['remove_comments'])
            modified = process_m3u8_file(filename, cfg)
            lib.prnt.param('Modified:', modified)


def process_m3u8_file(filename, cfg):
    """
    Process an m3u8 file.
    """
    # Init
    modified = False
    m3u8_file = open(filename, 'r+')
    lines = list(m3u8_file)
    i = 0
    # Process
    while i < len(lines):
        line = lines[i]
        if (cfg['add_closed_captions_none']
                and line.startswith('#EXT-X-STREAM-INF')
                and line.find('CLOSED-CAPTIONS') == -1):
            lines[i] = line.strip('\r\n') + ',CLOSED-CAPTIONS=NONE' + os.linesep
            modified = True
        if (cfg['remove_comments']
                and line.startswith('#')
                and not line.startswith('#EXT')):
            del lines[i]
            modified = True
            i -= 1
        i += 1
    # Write m3u8 if necessary
    if modified:
        m3u8_file.seek(0)
        m3u8_file.truncate()
        m3u8_file.writelines(lines)
    # Close m3u8
    m3u8_file.close()
    return modified
