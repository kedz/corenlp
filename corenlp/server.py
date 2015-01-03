# coding=utf-8

import os
import socket
import pkg_resources
import subprocess
from StringIO import StringIO
from .file_reader import read_xml
import corenlp.util
import time

# Client-Server protocal codes
CHECK_IN = 'c'
ANNOTATE = 'a'
QUIT = 'q'
SUCCESS = 'SUCCESS'
BUFFER_SIZE = 1024

class CoreNLPClient:

    def __init__(self, port=10999):
        self.host = u'localhost'
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(15)
        self._num_retries = 3

        connected = False
        n_try = 0
        while not connected and n_try < self._num_retries:
            try:
                self.sock.connect((self.host, self.port))
                self.sock.sendall(CHECK_IN)
                data = self.sock.recv(BUFFER_SIZE)
                assert data == SUCCESS
                self.sock.close()
                connected = True
            except socket.error, e:    
                if u'[Errno 111] Connection refused' == unicode(e):
                    import sys
                    err = sys.stderr
                    err.write(u'Could not find CoreNLP server on {}:{}\n'.format(
                        self.host, self.port))
                    err.flush()
                    sys.exit()
                elif '[Errno 99] Cannot assign requested address' in str(e):
                    print e
                    print "sleeping for 3 seconds..."
                    time.sleep(3)
            n_try += 1
             
                
    def annotate(self, text, xml=False):

        if isinstance(text, unicode):
            text = text.encode('utf-8')
        
        connected = False
        for i in range(self._num_retries):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(15)
                self.sock.connect((self.host, self.port))
                connected = True
                break
            except socket.error, e:
                if i > 2:
                    print "try:", i, str(e)
                time.sleep(5)
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

def start(port=10999, mem=u'3G', annotators=None, threads=1,
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

    java_home = os.getenv("JAVA_HOME", None)
    if java_home is None:
        java_cmd = "java"
    else:
        java_cmd = os.path.join(java_home, "bin", "java")

    cpath = corenlp.util.validate_jars(cnlp_dir, cnlp_ver)
    cpath = u'{}:{}'.format(cpath, 
                            pkg_resources.resource_filename("corenlp", "bin"))

    args = [u'nohup', java_cmd, u'-Xmx{}'.format(mem), u'-cp', cpath,
            u'CoreNlpServer', u'-p', str(port), u'-t', str(threads)]

    if annotators is not None:
        args.extend([u'-a', u','.join(annotators)])
    args.append('>corenlp.log 2>&1 &')
    
    cmd = ' '.join(args)

    subprocess.Popen(cmd, shell=True)

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

def stop(port=10999):
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

def check_status(port=10999):
    server_on = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', port))
        s.sendall(CHECK_IN)
        data = s.recv(BUFFER_SIZE)
        if data == SUCCESS:
            server_on = True
        s.close()
    except socket.error, e:    
        pass
    return server_on

if __name__ == u'__main__':
    start()
