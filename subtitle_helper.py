# coding: utf-8

import collections
import re
import warnings

from utils import unnext

Subtitle = collections.namedtuple('Subtitle', ['start', 'end', 'text', 'video'])

re_time = re.compile(r'(?P<start>(?:[0-9]+\:)*[0-9]+\.[0-9]+)\s+-->\s+(?P<end>(?:[0-9]+\:)*[0-9]+\.[0-9]+)')
re_timestamp = re.compile(r'(?:(?:(?P<hours>[0-9]+):)?(?:(?P<minutes>[0-9]+):))?(?P<seconds>[0-9]+\.[0-9]+)')

def _parse_timestamp(timestamp):
    m = re_timestamp.match(timestamp)
    hours = m.group('hours') or 0
    minutes = m.group('minutes') or 0
    seconds = m.group('seconds')
    total = float(seconds) + 60.0 * float(minutes) + 3600.0 * float(hours)
    return int(total * 1000)

def _gather_cues(webvtt):
    lines = iter(webvtt.splitlines())
    while True:
        line = next(lines).strip()
        if line.startswith('WEBVTT'):
            continue
        if line.startswith('NOTE'):
            continue
        if line.isspace():
            continue
        lines = unnext(lines, line)
        break

    current_cue = None
    while True:
        try:
            line = next(lines).strip()
            if not line:
                continue
            if line.isspace():
                continue
            if line.startswith('NOTE'):
                continue
            m = re_time.match(line)
            if m is not None:
                current_cue = (
                    _parse_timestamp(m.group('start')),
                    _parse_timestamp(m.group('end'))
                )
            else:
                if current_cue is None:
                    warnings.warn('Found subtitles before timestamp data in WebVTT info')
                    continue
                else:
                    yield Subtitle(current_cue[0], current_cue[1], line, None)
        except StopIteration:
            break

def gather_cues(webvtt):
    gen = _gather_cues(webvtt)
    last = None
    while True:
        try:
            if last is None:
                last = next(gen)
                continue
            current = next(gen)
            if last.text == current.text:
                last = Subtitle(last.start, current.end, last.text, last.video)
            else:
                yield last
                last = current
        except StopIteration:
            if last is not None:
                yield last
            break

def search(subtitles, word):
    word = word.strip().lower()
    for subtitle in subtitles:
        words = subtitle.text.lower().replace('-', ' ').split()
        if word in words:
            yield subtitle

def to_string(subtitle):
    return '{:0.3f}s to {:0.3f}s in "{}"'.format(
        subtitle.start / 1000.0,
        subtitle.end / 1000.0,
        subtitle.video
    )

if __name__ == '__main__':
    import sys
    input_webvtt = sys.stdin.read()
    for subtitle in gather_cues(input_webvtt):
        print(subtitle)
