from zope.interface.declarations import implements

import MySQLdb 
import pgsql
from groovecubes.webmail.interfaces import IMailserverUserManager
from imapclient.imapclient import IMAPClient
from groovecubes.webmail.errors import NoAccountError, NoEmailAddressError

import logging

class DBMail2UserManager:
    implements(IMailserverUserManager)
    
    Logger = logging.getLogger("groovecubes.webmail")
    
    def __init__(self, id, **config):
        self.id = id
        self.host = config['host']
        self.port = config['port']
        self.ssl = config.get('ssl', False)
        
        
        additional_args = config['mailserver_args']
        
        if additional_args.has_key('port'):
            additional_args['port'] = int(additional_args['port'])
            
        if additional_args['backend'] == "mysql":
            del additional_args['backend']    
            self.db = MySQLdb.connect(**additional_args)
        else:
            # not tested
            self.db = pgsql.connect(**additional_args)
                 
        self.config = config
        self.cursor = self.db.cursor()
        
    def addUser(self, login, password, aliases, max_mailbox_size):
        
        query = """INSERT INTO dbmail_users 
                       (userid, passwd, client_idnr, maxmail_size,
                        encryption_type, last_login) 
                   VALUES 
                   ('%s', '%s', 0, '%s','', NOW())
                   """ % (login, password, max_mailbox_size * 1024000, )
                   
        self.cursor.execute(query)
        self.db.commit()
        
        query = """ SELECT user_idnr 
                    FROM dbmail_users
                    WHERE userid = '%s'""" % login
        self.cursor.execute(query)    
        id = self.cursor.fetchall()[0][0]
        
        ## create the mailbox
        query = """ INSERT INTO dbmail_mailboxes 
                     (name, owner_idnr,seen_flag, answered_flag, 
                      deleted_flag,flagged_flag, recent_flag, 
                      draft_flag, permission) 
                    VALUES 
                   ('INBOX', %d, 1, 1, 1, 1, 1, 1, 2)""" % int(id)
        self.cursor.execute(query)
        self.db.commit()
        
        for alias in aliases:
            self.addAlias(id, alias)
                   
        
    def updateUser(self, id, login, quota, aliases):
        query = """ UPDATE dbmail_users
                    SET userid = '%s',
                        maxmail_size = %d
                    WHERE user_idnr = %d 
                """ % (login, quota * 1024000, id)
        self.cursor.execute(query)
        self.db.commit()
        
        cur_aliases = self.getAliases(id)
        ## add new aliases
        for alias in aliases:
            if not alias in cur_aliases and not alias in ('formhelper',''):
                self.addAlias(id, alias)
        ## remove unwanted aliases
        for alias in cur_aliases:
            if not alias in aliases:
                self.removeAlias(id, alias) 
    
    
    def removeUser(self, id):
        query = """ """
        
    
    def setPassword(self, id, password):
        """Change the users password"""
        query = """ """
        
        
    def getCredentials(self, login):
        query = """ SELECT passwd,encryption_type
                    FROM dbmail_users
                    WHERE userid = '%s'""" % login
                    
        if not self.cursor.execute(query):
            return False
        
        cred = self.cursor.fetchall()
        return cred[0] 
        
    
    def addAlias(self, id, alias):
        query = """INSERT INTO dbmail_aliases
                    (alias, deliver_to, client_idnr)
                   VALUES
                    ('%s','%s', 0)""" % (alias, id)
        
        self.cursor.execute(query)
        self.db.commit()
          
    
    def removeAlias(self, id, alias):
        query = """DELETE FROM dbmail_aliases
                   WHERE alias = '%s'
                   AND
                   deliver_to = %d """ % (alias, id)
        self.cursor.execute(query)
        self.db.commit()
        
        
    def getAliases(self, id):
        query = "SELECT alias FROM dbmail_aliases WHERE deliver_to = %d" % int(id)
        self.cursor.execute(query)
        aliases = []
        for alias in self.cursor.fetchall():
            aliases.append(alias[0])
        
        return aliases
        
            
    def getUserList(self):
        """ 
        This is mostly for the user management on the email server. 
        """
        query = """SELECT user_idnr, userid, maxmail_size, 
                          curmail_size, encryption_type, dbmail_aliases.alias 
                    FROM dbmail_users 
                    JOIN  dbmail_aliases 
                    WHERE dbmail_users.user_idnr = dbmail_aliases.deliver_to"""
        
        self.cursor.execute(query)
        users = {}
      
        for row in self.cursor.fetchall():
            if not users.has_key(row[1]):
                users[row[1]] = {'id':row[0],
                                 'login':row[1],
                                 'aliases': [row[5]],
                                 'quota_max_mb':row[2],
                                 'quota_cur_mb':row[3],
                                 'encrypt': row[4] 
                                 }
            else:
                users[row[1]]['aliases'].append(row[5])
        return users
    
    
    def authenticateCredentials(self, login, password):
        """ 
        Authenticate a user against the imap server, to verify
        him as plone user.
        """
        server = IMAPClient(self.host, use_uid=True, ssl=self.ssl)
        try:
            server.login(login, password)
            server.logout()
            return True
         
        except StandardError, e:
            self.Logger.info("login failed")
            
        return False
    
    def enumerateUsers(self, **kwargs):
        """ -> ( user_info_1, ... user_info_N )

        o Return mappings for users matching the given criteria.

        o 'id' or 'login', in combination with 'exact_match' true, will
          return at most one mapping per supplied ID ('id' and 'login'
          may be sequences).

        o If 'exact_match' is False, then 'id' and / or login may be
          treated by the plugin as "contains" searches (more complicated
          searches may be supported by some plugins using other keyword
          arguments).

        o If 'sort_by' is passed, the results will be sorted accordingly.
          known valid values are 'id' and 'login' (some plugins may support
          others).

        o If 'max_results' is specified, it must be a positive integer,
          limiting the number of returned mappings.  If unspecified, the
          plugin should return mappings for all users satisfying the criteria.

        o Minimal keys in the returned mappings:

          'id' -- (required) the user ID, which may be different than
                  the login name

          'login' -- (required) the login name

          'pluginid' -- (required) the plugin ID (as returned by getId())

          'editurl' -- (optional) the URL to a page for updating the
                       mapping's user

        o Plugin *must* ignore unknown criteria.

        o Plugin may raise ValueError for invalid criteria.

        o Insufficiently-specified criteria may have catastrophic
          scaling issues for some implementations.
        
        +++
        
        At this point, we already checked for login and/or id not to be None
        
        +++
        """
        print kwargs
         
        key = kwargs.get('id') or kwargs.get('login')
        
        query = """ SELECT userid, passwd  
                    FROM dbmail_users 
                    WHERE userid = '%s' """ % key 
        
        #if kwargs.get("exact_match"):
        #    self.cursor.
        
        return [{'id' : '',
                 'login' : '',
                 'pluginid' : kwargs.get('pluginid'),
                 'editurl': '/edit_mx1'
               }]
        
        
        
        
    
    def getIMAPConnection(self, login):
        if not login:
            raise NoEmailAddressError(login)
        
        cred = self.getCredentials(login)
        if not cred:
            raise NoAccountError(login)
        
        server = IMAPClient(self.host, use_uid=True, ssl=self.ssl)
        server.login(login, cred[0])
        return server
    