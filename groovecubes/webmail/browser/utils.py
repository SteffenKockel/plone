import re
from email.parser import HeaderParser 
from email import header as MessageHeader

from groovecubes.webmail.config import CHARSETS


""" helper methods for the webmail addon to deal with encodings, headers
    and body parsing.  """

def parsePlaintextEmailBody(body, encoding, ignore=False):
    """ Parse a plaintext email, replacing link-texts with 
        valid html-links
    
    @param body: the body of an email (message.get_payload()). 
    
    @param encoding: the encoding of the body.
    
    @return: unicode email body"""
        
    # linebreaks
    body = re.sub(r"\r?\n","<br />", body.strip())
    #body = body.replace('\r\n', '<br/>')
    #body = body.replace('\n', '<br/>')
    # links
    r = re.compile(r"(https?://[^\s<]+)", re.M)
    body = r.sub(r'<a target="_blank" href="\1">\1</a>', body)
    
    if ignore:
        return unicode(body, encoding, 'ignore')
    
    try:
        return unicode(body, encoding)
    except (UnicodeDecodeError,TypeError,LookupError), e:
        
        for c in CHARSETS:
            
            try:
                return unicode(body, c)
            except UnicodeDecodeError:
                continue
            
            return unicode(body, CHARSETS[0], 'ignore')  
    
    
    
    


def parseHTMLEmailBody(body, encoding, tags=None):
    """ Used to strip certain tags from incoming html 
        messages. 
        
    @param body: the body of an email (message.get_payload()). 
    
    @param encoding: the encoding of the body.
    
    @param tags: list of html-tags to strip (defaults to:
                 [ 'frame','iframe','script','form' ]
    
    @return: unicode email body 
    
    """ 
    if not tags:
        tags = ['frame','iframe','script','form']
    
    for tag in tags:
        r = re.compile(r"(<%s>.*</%s>)" % (tag, tag))
        body = r.sub('', body)
        
    return unicode(body, encoding)
        

def parseHeadersFromString(headers):
    """ Parses all headers from a string (BODY[HEADER])
    
    @param headers: string that represents an email header
    
    @return: python email message object 
    
    """
    P = HeaderParser()
    return P.parsestr(headers, headersonly=True)


def decodeHeader(header, charset=None):
    """ Decodes base64 encoded header part, e.g. "subject" or "From" 
    
    @param encoded_string: the encoded header part of an email
                           parsed by parseHeadersFromString().
                           
    @param charset: the charset this string is encoded with.
    
    @return: unicode string of header 
    
    """
    
    parts = []
    for part in MessageHeader.decode_header(header):
        try:
            text = part[0].decode(part[1] or charset or 'UTF-8')
        except (UnicodeDecodeError,LookupError), e:
            for c in CHARSETS:
                try:
                    text = part[0].decode(c)
                    break
                except UnicodeDecodeError, e:
                    continue
        # hope this does not cause any errors later.
        parts.append(text)
    
    return ' '.join(parts)

