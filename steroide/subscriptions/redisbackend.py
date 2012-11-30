from redistogo import r

def subscription(clients, prefix="steroide", channel="steroide"):
    pubsub = r.pubsub()
    pubsub.subscribe('%s:%s' % (prefix, channel))
    for message in pubsub.listen():
        if message['type'] in ['message', 'pmessage']:
            data = message['data']
            for client in clients: # should not send to all ofc. TODO!
                clients[client].publish(data)