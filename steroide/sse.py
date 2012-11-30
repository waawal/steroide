class SSE(object):

    def __init__(self, connection, retry=2000):
        self._connection = connection
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
        if event_id is not None:
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

    def publish_raw(self, data):
        self._connection.put(data)
    
    def __str__(self):
        if sys.version_info[0] >= 3: # Python 3
            return self.__unicode__()
        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        return "".join(self._connection)

    def __iter__(self):
        for item in self._connection:
            yield item