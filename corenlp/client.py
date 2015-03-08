import socket
import signal
import multiprocessing
import Queue
import corenlp.protocol as p
from StringIO import StringIO
from .file_reader import read_xml
from itertools import izip

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


    def annotate_mp(self, texts, keys=None, input=u"content", n_procs=2, return_xml=False):
        results_iter = self.annotate_mp_iter(
            texts, keys=None, input=input, n_procs=n_procs, return_xml=return_xml)
        results = [result for result in results_iter]
        return keys, results

    def annotate_mp_iter(self, texts, keys=None, input=u"content", 
                         n_procs=2, return_xml=False):
        max_jobs = len(texts)
        if keys is not None:
            assert len(keys) == len(texts)
        
        results = [None] * max_jobs
        orders = range(0, max_jobs)
        job_iter = self.annotate_mp_unordered_iter(
            texts, keys=orders, input=input, n_procs=n_procs, 
            return_xml=return_xml)
        for i in xrange(max_jobs):
            while results[i] is None:
                order, result = next(job_iter)
                results[order] = result
            if keys is None:
                yield results[i]
            else:
                yield keys[i], results[i]

    def annotate_mp_unordered_iter(self, texts, keys=None, input=u"content", 
                                   n_procs=2, return_xml=False):
        if keys is not None:
            has_key = True
            assert len(keys) == len(texts)
            jobs = [(key, text) 
                    for (key, text) in izip(keys, texts)] 
        else:
            has_key = False
            jobs = texts
            #jobs = [(jid, text) for jid, text in enumerate(texts)] 
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
                    u'return_xml': return_xml, u'has_key': has_key,
                    u'input': input})
            p.start()
            pool.append(p)

        try:
            #results = [None] * max_jobs 
            if has_key is True:
                for n_job in xrange(max_jobs):
                    key, result = result_queue.get(block=True)
                    yield key, result
            else:
                for n_job in xrange(max_jobs):
                    result = result_queue.get(block=True)
                    yield result

            for p in pool:
                p.join()

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
    has_key = kwargs.get(u'has_key') 
    input = kwargs.get(u'input')
    client = CoreNLPClient(host=host, port=port, verbose=verbose)

    while not job_queue.empty():
        try:
            if has_key is True:
                key, job = job_queue.get(block=False)
                if input == u'content':
                    text = job
                elif input == u'filename':
                    with open(job, u'r') as f:
                        text = ''.join(f.readlines())
                result = client.annotate(text, return_xml=return_xml)    
                result_queue.put((key, result))

            else:
                job = job_queue.get(block=False)
                if input == u'content':
                    text = job
                elif input == u'filename':
                    with open(job, u'r') as f:
                        text = ''.join(f.readlines())

                result = client.annotate(text, return_xml=return_xml)    
                result_queue.put(result)
        except Queue.Empty:
            pass
