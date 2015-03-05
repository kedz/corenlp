import socket
import signal
import multiprocessing
import Queue
import corenlp.protocol as p
from StringIO import StringIO
from .file_reader import read_xml

class CoreNLPClient(object):
    def __init__(self, host="localhost", port=9989, verbose=False):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_ = False
        self.verbose_ = verbose

    def annotate(self, str_or_unicode, return_xml=False):
        if isinstance(str_or_unicode, unicode):
            if self.verbose_:
                print "cnlpclient :: converting encoding unicode as bytes"
            text = str_or_unicode.encode(u'utf-8')
        else:
            text = str_or_unicode
        
        if not self.connected_:
            if self.verbose_:
                print "cnlpclient :: connection to {}:{}".format(
                    self.host, self.port)
            self.connect()

        self.sock.sendall(p.tokens.annotate) 
        self.sock.sendall(text)
        self.sock.sendall(p.tokens.eof)

        xml = self._receive()
        
        if return_xml is True:
            return xml.decode(u'utf-8')
        else:   
            buf = StringIO(xml)      
            return read_xml(buf)
 

    def connect(self):
        self.sock.connect((self.host, self.port))
        self.connected_ = True
        return 

    def _receive(self):
        buf = ''
        while 1:
            chunk = self.sock.recv(8192)
            buf += chunk
            if chunk[-1] == b'\0':
                break
        return buf[:-1]

    def shutdown(self):
        if not self.connected_:
            if self.verbose_:
                print "cnlpclient :: connection to {}:{}".format(
                    self.host, self.port)
            self.connect()

        self.sock.sendall(p.tokens.shutdown) 
        self.sock.sendall(p.tokens.eof)

    def annotate_mp(self, texts, n_procs=2, return_xml=False):
        jobs = [(key, text) for key, text in enumerate(texts)] 
        max_jobs = len(jobs)
        manager = multiprocessing.Manager()
        job_queue = manager.Queue()
        result_queue = manager.Queue()

        for job in jobs:
            job_queue.put(job)

        pool = []
        for i in xrange(n_procs):
            p = multiprocessing.Process(
                target=process_worker, args=(job_queue, result_queue),
                kwargs={u'host': self.host, u'port': self.port, 
                    u'return_xml': return_xml})
            p.start()
            pool.append(p)

        try:
            results = [None] * max_jobs 
            for n_job in xrange(max_jobs):
                key, result = result_queue.get(block=True)
                results[key] = result

            for p in pool:
                p.join()

            return results

        except KeyboardInterrupt:
            print "Completing current jobs and shutting down!"
            while not job_queue.empty():
                job_queue.get()
            for p in pool:
                p.join()
            sys.exit()

def process_worker(job_queue, result_queue, **kwargs):
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    port = kwargs.get(u'port')
    host = kwargs.get(u'host')
    verbose = kwargs.get(u'verbose')
    return_xml = kwargs.get(u'return_xml') 
    client = CoreNLPClient(host=host, port=port, verbose=verbose)

    while not job_queue.empty():
        try:
            key, str_or_uni = job_queue.get(block=False)
            result = client.annotate(str_or_uni, return_xml=return_xml)    
            result_queue.put((key, result))
        except Queue.Empty:
            pass
