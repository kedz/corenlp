import os
import tempfile
import subprocess

_default_annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'dcoref']
_default_mem = '2500m'
_default_libver = '3.2.0'
_pipeline_class = 'edu.stanford.nlp.pipeline.StanfordCoreNLP'

def dir2dir(in_dir, out_dir=None, annotators=None, mem=None, libdir=None, libver=None, threads=1):
    
    if out_dir is None:
        out_dir = '.'

    if annotators is None:
        annotators = _default_annotators

    if mem is None:
        mem = _default_mem
    
    if libdir is None:
        libdir = os.getenv('CORENLP_HOME', '.')

    if libver is None:
        libver = os.getenv('CORENLP_VER', _default_libver)        
    
    filelist = _build_filelist(in_dir)

    cpath = _build_classpath(libdir, libver)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    cmd = 'java -Xmx{} -cp {} {} '\
          '-annotators {} -filelist {} '\
          '-outputDirectory {} -threads {}'.format(mem, cpath, 
                                                   _pipeline_class,
                                                   ','.join(annotators),
                                                   filelist.name, out_dir,
                                                   threads)
    subprocess.check_output(cmd, shell=True)
    filelist.close()
    
    
        
def _build_classpath(libdir, libver):

    jars = ['joda-time.jar',
            'jollyday.jar',
            'stanford-corenlp-{}.jar'.format(libver),
            'stanford-corenlp-{}-models.jar'.format(libver),
            'xom.jar']

    jarpaths = []
    for jar in jars:
        jarpath = os.path.join(libdir, jar)
        if not os.path.exists(jarpath):
            import sys
            sys.stderr.write('Fatal Error: could not locate corenlp jar {}\n'.format(jarpath))
            sys.stderr.flush()
            sys.exit()
        jarpaths.append(jarpath)
    return ':'.join(jarpaths)

def _build_filelist(in_dir):
    filelist = tempfile.NamedTemporaryFile()
    for txt_file in os.listdir(in_dir):
        filename = os.path.join(in_dir, txt_file)
        filelist.write(filename)
        filelist.write('\n')
    filelist.flush()
    return filelist
