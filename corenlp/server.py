# coding=utf-8

import os
import socket
import pkg_resources
import subprocess
from StringIO import StringIO
from .file_reader import read_xml
import corenlp.util

# Client-Server protocal codes
CHECK_IN = 'c'
ANNOTATE = 'a'
QUIT = 'q'
SUCCESS = 'SUCCESS'
BUFFER_SIZE = 1024

class CoreNLPClient:

    def __init__(self, port=8090):
        self.host = u'localhost'
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._num_retries = 3

        try:
            self.sock.connect((self.host, self.port))
            self.sock.sendall(CHECK_IN)
            data = self.sock.recv(BUFFER_SIZE)
            assert data == SUCCESS
            self.sock.close()
        except socket.error, e:    
            if u'[Errno 111] Connection refused' == unicode(e):
                import sys
                err = sys.stderr
                err.write(u'Could not find CoreNLP server on {}:{}\n'.format(
                    self.host, self.port))
                err.flush()
                sys.exit()

    def annotate(self, text, xml=False):

        if isinstance(text, unicode):
            text = text.encode('utf-8')
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        connected = False
        for i in range(self._num_retries):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(15)
                self.sock.connect((self.host, self.port))
                connected = True
                break
            except socket.error, e:
                print "try:", i, str(e)
        if not connected:
            raise Exception("Failed to connect to server.")

        self.sock.settimeout(None)
        message_size = len(text)
        #print "ACTUAL MESSAGE SIZE:", message_size
        self.sock.sendall('{}{} {}'.format(ANNOTATE, message_size, text))
        self.sock.shutdown(socket.SHUT_WR)

        resp = self.sock.recv(BUFFER_SIZE)
        resp = resp.split(' ', 1)

        buf = resp[1]       
        message_size = int(resp[0])
        read_bytes = len(buf)

        while read_bytes < message_size:
            resp = self.sock.recv(BUFFER_SIZE)
            read_bytes += len(resp)
            buf += resp
        self.sock.close()
        if xml is True:
            return buf
        else:
            return read_xml(StringIO(buf))

def start(port=8090, mem=u'3G', annotators=None, threads=1,
          server_start_timeout=60):
    
    cnlp_dir = os.environ.get('CORENLP_DIR')
    cnlp_ver = os.environ.get('CORENLP_VER')
    if cnlp_dir is None:
        raise MissingJavaLibException(
            u'Set CORENLP_DIR environment variable to the CoreNLP directory.')
    if cnlp_ver is None:
        raise MissingJavaLibException(
            u'Set CORENLP_VER environment variable to the CoreNLP version' + \
            u' (format "X.X.X").')

    cpath = corenlp.util.validate_jars(cnlp_dir, cnlp_ver)
    cpath = u'{}:{}'.format(cpath, 
                            pkg_resources.resource_filename("corenlp", "bin"))

    args = [u'nohup', u'java', u'-Xmx{}'.format(mem), u'-cp', cpath,
            u'CoreNlpServer', u'-p', str(port), u'-t', str(threads)]

    if annotators is not None:
        args.extend([u'-a', u','.join(annotators)])
    args.append('>corenlp.log 2>&1 &')
    
    cmd = ' '.join(args)

    subprocess.Popen(cmd, shell=True)

    import socket
    import time
    server_on = False
    start = time.time()
    duration = time.time() - start

    while duration < server_start_timeout and server_on is False:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', port))
            s.sendall(CHECK_IN)
            data = s.recv(BUFFER_SIZE)
            assert data == SUCCESS
            s.close()
            server_on = True
        except socket.error, e:    
            pass

        time.sleep(1)
        duration = time.time() - start

def stop(port=8090):
    host = u'localhost'
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
        sock.sendall(QUIT)
        data = sock.recv(BUFFER_SIZE)
        assert data == SUCCESS
        sock.close()
    except socket.error, e:    
        if u'[Errno 111] Connection refused' == unicode(e):
            raise Exception(u'Could not find CoreNLP server on {}:{}\n'.format(
                host, port))


if __name__ == u'__main__':
    start()
