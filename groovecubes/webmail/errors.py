from groovecubes.webmail import MessageFactory as _

class NoAccountError(Exception):
    def __init__(self, user, msg=False):
        if not msg: 
            msg = 'User "%s "has no account on this server' % user
        Exception.__init__(self, msg)