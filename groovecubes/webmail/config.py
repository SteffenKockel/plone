"""Common configuration constants
"""

PROJECTNAME = 'groovecubes.webmail'

# fallback charsets
CHARSETS = ['UTF-8', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10',
            'us-ascii', 'ascii', 'cp1250', 'Windows-1252', 'Windows-1250', 'UTF-16',
            'UTF32']

# some shortcuts for field policies
NO_NO = {"edit": "invisible", "view": "invisible"}
NO_YES = {"edit": "invisible", "view": "visible"}
YES_YES = {"edit": "visible", "view": "visible"}
YES_NO = {"edit": "visible", "view": "invisible"}


# Fetch header list from current folder
        # XXX: make details configurable via ZMI
MESSAGE_PREVIEW_DETAILS = ['BODY[HEADER]','FLAGS','INTERNALDATE', 'RFC822.SIZE','BODYSTRUCTURE']

ADD_PERMISSIONS = {
    # -*- extra stuff goes here -*-
'IMAPServer': 'groovecubes.webmail: Add IMAPServer',
    'Webmail': 'groovecubes.webmail: Add Webmail',
}
