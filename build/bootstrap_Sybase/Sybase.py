class DummyConnection(object):
    def __init__(self):
        self._is_connected = True

def connect(*args, **kwargs):
    return DummyConnection()
