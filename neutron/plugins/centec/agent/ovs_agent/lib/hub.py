#!/usr/bin/env python
# encoding: utf-8

import eventlet
import eventlet.event
import eventlet.queue
import eventlet.timeout
import eventlet.wsgi
import greenlet

getcurrent = eventlet.getcurrent
patch = eventlet.monkey_patch
sleep = eventlet.sleep
socket = eventlet.green.socket
Queue = eventlet.queue.Queue
QueueEmpty = eventlet.queue.Empty
Semaphore = eventlet.semaphore.Semaphore
BoundedSemaphore = eventlet.semaphore.BoundedSemaphore
Event = eventlet.event.Event


def spawn(*args, **kwargs):
    def _launch(func, *args, **kwargs):
        # mimic gevent's default raise_error=False behaviour
        # by not propergating an exception to the joiner.
        try:
            func(*args, **kwargs)
        except greenlet.GreenletExit:
            pass
        except:
            # log uncaught exception.
            # note: this is an intentional divergence from gevent
            # behaviour.  gevent silently ignores such exceptions.
            # LOG.error('hub: uncaught exception: %s',
            #          traceback.format_exc())
            pass

    return eventlet.spawn(_launch, *args, **kwargs)


class StreamServer(object):
    def __init__(self, listen_info, handle=None, backlog=None):
        assert backlog is None

        self.server = eventlet.listen(listen_info)
        self.handle = handle

    def serve_forever(self):
        while True:
            sock, addr = self.server.accept()
            spawn(self.handle, sock, addr)


def kill(thread):
    thread.kill()


def cancel(thread):
    thread.cancel()


def joinall(threads):
    for t in threads:
        # this try-except is necessary when killing an inactive
        # greenthread
        try:
            t.wait()
        except greenlet.GreenletExit:
            pass
