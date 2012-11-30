# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys
import signal

import gevent
from gevent.queue import Queue
from gevent.pywsgi import WSGIHandler, WSGIServer

from sse import SSE
from subscriptions.redisbackend import subscription

class Steroide(WSGIHandler):
    'docstr'
    __connected_clients = {} # wekref ??? - sequence of conns for each key or to be used with set theory?
    gevent.spawn(subscription, __connected_clients)

    def __init__(self, *args, **kwargs):
        gevent.spawn(self.keep_alive) # TODO: Allow for custom timeout, allready in method signature.
        super(Steroide, self).__init__(*args, **kwargs)

    def process_result(self):
        'docstr'
        
        try:
            # TODO: Check if already in dict, if so - hang up!
            self.__connected_clients[self.path] = self.result
            super(Steroide, self).process_result()
        except gevent.socket.error, e:
            if e.errno != 32: # error: [Errno 32] Broken pipe
                raise
        finally: 
            if self.path in self.__connected_clients:
                del self.__connected_clients[self.path]

    def keep_alive(self, interval=15):
    # should be connected to a connection and respawned based on last data sent
        'docstr'
        while True:
            gevent.sleep(interval)
            for connection in self.__connected_clients.values():
                connection.publish_raw(":\n\n")

def wsgi_app(env, start_response):
    'docstr'
    start_response('200 OK', [('Content-Type', 'text/event-stream'),
                              ('Cache-Control', 'no-cache'),
                              ('Access-Control-Allow-Origin', '*')]) # TODO: customize CORS!!!
    return SSE(Queue())

if __name__ == '__main__':
    gevent.signal(signal.SIGQUIT, gevent.shutdown)
    WSGIServer(('', 8088), wsgi_app, handler_class=Steroide).serve_forever()