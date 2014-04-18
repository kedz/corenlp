import os
import tempfile
import subprocess

_default_annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'dcoref']
_default_mem = '2500m'
_default_libver = '3.2.0'
_default_threads = 1
_pipeline_class = 'edu.stanford.nlp.pipeline.StanfordCoreNLP'


def dir2dir(in_dir, out_dir=None, annotators=None, mem=None,
            libdir=None, libver=None, threads=None):

    files = []
    for txt_file in os.listdir(in_dir):
        fpath = os.path.join(in_dir, txt_file)
        files.append(fpath)

    files2dir(files, out_dir=out_dir, annotators=annotators,
              mem=mem, libdir=libdir, libver=libver,
              threads=threads)


def files2dir(files, out_dir=None, annotators=None,
              mem=None, libdir=None, libver=None, threads=None):
    
    filelist = _build_filelist(files)    

    if out_dir is None:
        out_dir = '.'    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if annotators is None:
        annotators = _default_annotators
        
    if mem is None:
        mem = _default_mem           

    if libdir is None:
        libdir = os.getenv('CORENLP_HOME', '.')

    if libver is None:
        libver = os.getenv('CORENLP_VER', _default_libver)        

    if threads is None:
        threads = _default_threads                

    cpath = _build_classpath(libdir, libver)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    cmd = 'java -Xmx{} -cp {} {} '\
          '-annotators {} -filelist {} '\
          '-outputDirectory {} -threads {} '\
          '-replaceExtension'.format(mem, cpath, 
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
            'xom.jar',
            'ejml-0.23.jar']

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

def _build_filelist(filepaths):
    
    filelist = tempfile.NamedTemporaryFile()
    for filepath in filepaths:
        filelist.write(filepath)
        filelist.write('\n')
    filelist.flush()
    return filelist
