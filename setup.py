from setuptools import setup
import os
import imp
import sys
import shutil

def validate_deps():
    path = os.getenv(u'CORENLP_DIR', None)
    if path is None:
        print u'Set CORENLP_DIR environment variable to the CoreNLP directory.'
        sys.exit(1) 

    ver = os.getenv(u'CORENLP_VER', None)
    if ver is None:
        print u'Set CORENLP_VER environment variable to the version of CoreNLP.'
        sys.exit(1) 

    return path, ver

def build_server(corenlp_path, corenlp_ver):

    java_home = os.getenv("JAVA_HOME", None)
    if java_home is None:
        javac_cmd = "javac"
    else:
        javac_cmd = os.path.join(java_home, "bin", "javac")

    path = os.path.dirname(os.path.realpath(__file__))
    file, pathname, description = imp.find_module('util', [os.path.join(path, 'corenlp')])
    util = imp.load_module('util', file, pathname, description)
    file.close()
    classpath = util.validate_jars(corenlp_path, corenlp_ver)
    src = os.path.join(path, u"server-src", u"*.java")
    server_src = os.path.join(path, u"server-src", u"CoreNlpServer.java")
    handler_src = os.path.join(path, u"server-src", u"CoreNlpHandler.java")
    server_cla = os.path.join(path, u"server-src", u"CoreNlpServer.class")
    handler_cla = os.path.join(path, u"server-src", u"CoreNlpHandler.class")
    os.system('{} -cp {} {}'.format(javac_cmd, classpath, src))
    if not os.path.exists(server_src) or not os.path.exists(handler_src):
        print "Failed to build java server."
        sys.exit(1)
    else: 
        bin_dir = os.path.join(path, u'corenlp', u'bin')
        server_dest = os.path.join(bin_dir, u'CoreNlpServer.class')
        handler_dest = os.path.join(bin_dir, u'CoreNlpHandler.class')
        if not os.path.exists(bin_dir):
            os.makedirs(bin_dir)
        if os.path.exists(server_dest):
            os.remove(server_dest)
        if os.path.exists(handler_dest):
            os.remove(handler_dest)
        shutil.move(server_cla, bin_dir)
        shutil.move(handler_cla, bin_dir)

corenlp_path, corenlp_ver = validate_deps()
build_server(corenlp_path, corenlp_ver)

setup(
    name = 'corenlp',
    packages = ['corenlp'],
    version = '0.0.14',
    description = 'A python wrapper for the Stanford CoreNLP java library.',
    author='Chris Kedzie',
    author_email='kedzie@cs.columbia.edu',
    url='https://github.com/kedz/corenlp',
    install_requires=[
        'nltk',
    ],
    include_package_data=True,
    package_data={
        'corenlp': [os.path.join('bin', 'CoreNlpServer.class'),
                    os.path.join('bin', 'CoreNlpHandler.class'),]},

)
                    
