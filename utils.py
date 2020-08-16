# coding: utf-8

import asyncio
import os

def unnext(iterator, item):
    yield item
    yield from iterator

def async_callback(function):
    def wrapper(*args, **kwargs):
        asyncio.create_task(function(*args, **kwargs))
    return wrapper

def get_ext(filename):
    ext = os.path.splitext(filename)[1]
    if not ext:
        raise ValueError('"{}" has no extension'.format(filename))
    return ext[1:]

async def cancellable(awaitable, cancel_event):
    cancel_task = asyncio.create_task(cancel_event.wait())
    awaitable_task = asyncio.create_task(awaitable)
    done, pending = await asyncio.wait({cancel_task, awaitable_task}, return_when=asyncio.FIRST_COMPLETED)
    if (cancel_task not in done) and not awaitable_task.cancelled() and awaitable_task.done():
        return True, awaitable_task.result()
    if not awaitable_task.cancelled():
        awaitable_task.cancel()
    return False, None