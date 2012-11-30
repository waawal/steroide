# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys
import signal

import gevent
from gevent.queue import Queue
from gevent.pywsgi import WSGIHandler, WSGIServer

from redistogo import r



def subscription(clients, prefix="steroide", channel="steroide"):
    pubsub = r.pubsub()
    pubsub.subscribe('%s:%s' % (prefix, channel))
    for message in pubsub.listen():
        if message['type'] in ['message', 'pmessage']:
            data = message['data']
            for client in clients: # should not send to all ofc. TODO!
                clients[client].publish(data)


class SSE(object):

    def __init__(self, retry=2000):
        self._connection = Queue()
        self.set_retry(retry)
        self._connection.put(":%s\n" % (" "*2049)) # XDomainRequest (IE8, IE9)

    def set_retry(self, ms): # Property?
        """
        Set distinct retry timeout instead the default
        value.
        """
        self._retry = ms
        self._connection.put("retry: {0}\n\n".format(self._retry))

    def set_event_id(self, event_id):
        if event_id:
            self._connection.put("id: {0}\n\n".format(event_id))
        else:
            # Reset event id
            self._connection.put("id\n\n")

    def reset_event_id(self):
        """
        Send a reset event id.
        """
        self.set_event_id(None)

    def _parse_text(self, text, encoding):
        # parse text if is list, tuple or set instance
        if isinstance(text, (list, tuple, set)): # TODO: ABC ???
            for item in text:
                if isinstance(item, bytes):
                    item = item.decode(encoding)

                for subitem in item.splitlines():
                    yield subitem

        else:
            if isinstance(text, bytes):
                text = text.decode(encoding)

            for item in text.splitlines():
                yield item

    def publish(self, text, event=None, event_id=None, encoding='utf-8'):
        """
        Add messaget with eventname to the buffer.

        :param str event: event name
        :param str/list text: event content. Must be a str or list of str
        """
        if event_id is not None:
            self.set_event_id(event_id)
        if event is not None:
            self._connection.put("event: {0}\n".format(event))

        for text_item in self._parse_text(text, encoding):
            self._connection.put("data: {0}\n".format(text_item))

        self._connection.put("\n")

    def __str__(self):
        if sys.version_info[0] >= 3: # Python 3
            return self.__unicode__()
        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        return "".join(self._connection)

    def __iter__(self):
        for item in self._connection:
            yield item


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
                connection._connection.put(":\n\n")

def wsgi_app(env, start_response):
    'docstr'
    start_response('200 OK', [('Content-Type', 'text/event-stream'),
                              ('Cache-Control', 'no-cache'),
                              ('Access-Control-Allow-Origin', '*')]) # TODO: customize CORS!!!
        # TODO: Write a wrapper for the Q
    return SSE()

if __name__ == '__main__':
    gevent.signal(signal.SIGQUIT, gevent.shutdown)
    WSGIServer(('', 8088), wsgi_app, handler_class=Steroide).serve_forever()