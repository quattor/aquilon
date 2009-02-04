"""
    Useful subroutines that don't fit in any place to particularly for aquilon.

    Copyright (C) 2008 Morgan Stanley
    This module is part of Aquilon
"""
import os
import signal

def kill_from_pid_file(pid_file):
    if os.path.isfile(pid_file):
        f = open(pid_file)
        p = f.read()
        f.close()
        pid = int(p)
        print 'killing pid %s'%(pid)
        try:
            os.kill(pid, signal.SIGQUIT)
        except Exception,e:
            pass

def monkeypatch(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator
