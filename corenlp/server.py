import os
import pkg_resources
import subprocess
import socket
import corenlp.util
import time
import corenlp.protocol as p
import tempfile
from .client import CoreNLPClient

class Server(object):

    
    def __init__(self, port=9989, mem=u'3G', annotators=None, threads=1,
                 max_message_len=32768, server_start_timeout=60, 
                 corenlp_props=None, cnlp_dir=None, cnlp_ver=None):
        self.port = port
        self.mem = mem
        self.annotators = annotators
        self.threads = threads
        self.max_message_len = max_message_len
        self.server_start_timeout = server_start_timeout
        self.corenlp_props = corenlp_props
        self.cnlp_dir = cnlp_dir
        self.cnlp_ver = cnlp_ver

    def __enter__(self):
        start(port=self.port, mem=self.mem, annotators=self.annotators, 
              threads=self.threads, max_message_len=self.max_message_len, 
              server_start_timeout=self.server_start_timeout, 
              corenlp_props=self.corenlp_props, cnlp_dir=self.cnlp_dir, 
              cnlp_ver=self.cnlp_ver)
        return CoreNLPClient(port=self.port)      

    def __exit__(self, type, value, traceback):
        stop(port=self.port)

def start(port=9989, mem=u'3G', annotators=None, threads=1,
          max_message_len=32768, server_start_timeout=60, 
          corenlp_props=None, cnlp_dir=None, cnlp_ver=None):
   
    if cnlp_dir is None: 
        cnlp_dir = os.environ.get('CORENLP_DIR')
    if cnlp_ver is None:
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

    jars_path = pkg_resources.resource_filename("corenlp", "jars")
    cpath = ":".join([
        corenlp.util.validate_jars(cnlp_dir, cnlp_ver),
        os.path.join(jars_path, "netty-all-4.0.25.Final.jar"),
        os.path.join(jars_path, "cnlpserver.jar")])

    

    args = [u'nohup', java_cmd, u'-Xmx{}'.format(mem), u'-cp', cpath,
            u'edu.columbia.cs.nlp.CoreNLPServer', 
            u'-p', str(port), u'-t', str(threads), u'-l', str(max_message_len)]

    if annotators is not None:
        args.extend([u'-a', u','.join(annotators)])

    if corenlp_props is not None:
        if isinstance(corenlp_props, dict):
            props_file = tempfile.NamedTemporaryFile()
            for key, value in corenlp_props.items():
                props_file.write("{}={}\n".format(key, value))
            props_file.flush()
            args.append("--props")
            args.append(props_file.name)
        else:
            args.append("--props")
            args.append(corenlp_props)

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
            s.close()
            server_on = True
        except socket.error, e:    
            pass

        time.sleep(1)
        duration = time.time() - start

def stop(host=u'localhost', port=9989):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        sock.sendall(p.tokens.shutdown) 
        sock.sendall(p.tokens.eof)
    except socket.error, e:    
        if u'[Errno 111] Connection refused' == unicode(e):
            raise Exception(u'Could not find CoreNLP server on {}:{}\n'.format(
                host, port))


if __name__ == u'__main__':
    start()
