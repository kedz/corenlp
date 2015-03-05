
class Protocol(object):
    pass

tokens = Protocol()
tokens.eof = b'\0'
tokens.annotate = '<CNLPANNOTATE>'
tokens.shutdown = '<CNLPSHUTDOWN>'
tokens.status = '<CNLPSTATUS>'
