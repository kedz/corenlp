import sys
import socket
import signal
import multiprocessing
import Queue
import corenlp.protocol as p
from StringIO import StringIO
from .file_reader import read_xml
from itertools import izip

class CoreNLPClient(object):
    """This is the main class for interacting with the CoreNLP server."""
    
    def __init__(self, host="localhost", port=9989, verbose=False):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_ = False
        self.verbose_ = verbose

    def annotate(self, str_or_unicode, return_xml=False):
        """Annotate a string or unicode object.
           
           :param str_or_unicode: string to annotate
           :type str_or_unicode: str or unicode
           :param return_xml: if True return xml rather than a Document 
           :type return_xml: bool
           :rtype: Document or xml"""

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

    def annotate_mp(self, texts, keys=None, input=u"content", n_procs=2, return_xml=False):
        """Batch annotate a list of texts, using n_procs processes. n_procs should be <= 
        the number of threads available on the server. If input == "content", texts should be
        a list of strings. Else if input == "filename", texts is a list of valid paths to
        read from.
           
        :param texts: list of input texts to process
        :type texts: str or unicode
        :param input: type of texts (list of strings/unicodes or filenames)
        :type intput: str (content|filename)
        :param return_xml: if True return xml rather than Documents 
        :type return_xml: bool
        :param n_procs: number of processes to run in parallel
        :type n_procs: positive int
        :rtype: list of Documents or xml
        """
        results_iter = self.annotate_mp_iter(
            texts, keys=None, input=input, n_procs=n_procs, return_xml=return_xml)
        results = [result for result in results_iter]
        if keys is None:
            return results
        else:
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
                                   n_procs=2, return_xml=False, 
                                   show_progress=False):
        
        show_progress = False if not sys.stdin.isatty() else show_progress

        if keys is not None:
            has_key = True
            assert len(keys) == len(texts)
            jobs = [(key, text) 
                    for (key, text) in izip(keys, texts)] 
        else:
            has_key = False
            jobs = texts
        
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
            if has_key is True:
                for n_job in xrange(max_jobs):
                    key, result = result_queue.get(block=True)
                    if show_progress is True:
                        sys.stdout.write(
                            "corenlp pipeline {:6.2f}% complete\r" .format(
                                (n_job + 1) * 100. / max_jobs))
                        sys.stdout.flush()

                    yield key, result
            else:
                for n_job in xrange(max_jobs):
                    result = result_queue.get(block=True)
                    if show_progress is True:
                        sys.stdout.write(
                            "corenlp pipeline {:6.2f}% complete\r" .format(
                                (n_job + 1) * 100. / max_jobs))
                        sys.stdout.flush()

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
        if show_progress is True:
            sys.stdout.write("                                    \r")
            sys.stdout.flush()

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
