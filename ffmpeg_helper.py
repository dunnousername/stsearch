# coding: utf-8

import asyncio
import os

import subtitle_helper
from utils import cancellable

async def _run(exe, *cmd, stdin=b'', event=None):
    proc = await asyncio.create_subprocess_exec(
        exe, *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    proc.stdin.write(stdin)
    proc.stdin.write_eof()
    proc.stdin.close()

    if event is not None:
        done, result = await cancellable(proc.communicate(), event)
        if not done:
            proc.terminate()
            return None
        stdout, stderr = result
    else:
        stdout, stderr = await proc.communicate()
    print(stderr.decode())
    return stdout, stderr.decode()

async def _ffmpeg(*cmd, stdin=b''):
    return await _run('ffmpeg', *cmd, stdin=stdin)

async def ffmpeg(*cmd, input=None, file_input=None, format='matroska', format_out=None):
    format = get_format(format)
    if file_input is not None:
        stdout, stderr = await _ffmpeg('-i', file_input, *cmd, '-f', format_out or format, '-')
    else:
        stdout, stderr = await _ffmpeg('-f', format, '-i', '-', *cmd, '-f', format_out or format, '-', stdin=input)
    return stdout, stderr

async def _ffplay(*cmd, stdin=b'', event=None):
    return await _run('ffplay', *cmd, stdin=stdin, event=event)

async def ffplay(*cmd, input=None, file_input=None, format='matroska', event=None):
    format = get_format(format)
    if file_input is not None:
        await _ffplay(*cmd, file_input, event=event)
    else:
        await _ffplay('-f', format, *cmd, '-', stdin=input, event=event)

def get_format(format):
    if format in ['mkv', 'mka', 'mks']:
        return 'matroska'
    if format in ['avi', 'mov', 'mp4', 'mp3', 'ogg', 'matroska', 'wav']:
        return format
    raise ValueError('invalid format: ' + format)

async def trim(start, end, input=None, file_input=None, format='matroska', format_out='wav'):
    return await ffmpeg('-map', '0:a', '-ss', str(start) + 'ms', '-to', str(end) + 'ms', input=input, file_input=file_input, format=format, format_out=format_out)

async def load_subtitles(input=None, file_input=None, format='matroska'):
    stdout, stderr = await ffmpeg('-map', '0:s', input=input, file_input=file_input, format=format, format_out='webvtt')
    stdout = stdout.decode()
    return list(subtitle_helper.gather_cues(stdout))

async def play_sound(input=None, file_input=None, format='wav', event=None):
    return await ffplay('-nodisp', format=format, input=input, file_input=file_input, event=event)