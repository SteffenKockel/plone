from groovecubes.webmail import MessageFactory as _

class NoAccountError(Exception):
    def __init__(self, user, msg=False):
        if not msg: 
            msg = 'User "%s "has no account on this server' % user
        Exception.__init__(self, msg)
        
        
class NoEmailAddressError(Exception):
    def __init__(self, user, msg=False):
        if not msg: 
            msg = 'User "%s" has email address specified. Check permissions.' % user
        Exception.__init__(self, msg)


class NotInMailgroupError(Exception):
    def __init__(self, user, msg=False):
        if not msg: 
            msg = 'User "%s" does not belong to this webmails group. Check permissions.' % user
        Exception.__init__(self, msg)