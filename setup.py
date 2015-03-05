from setuptools import setup
import os
import imp
import sys
import shutil

def validate_deps():
    path = os.getenv(u'CORENLP_DIR', None)
    if path is None:
        print u'Set CORENLP_DIR environment var to the CoreNLP directory.'
        sys.exit(1) 

    ver = os.getenv(u'CORENLP_VER', None)
    if ver is None:
        print u'Set CORENLP_VER environment var to the version of CoreNLP.'
        sys.exit(1) 
    return path, ver

def build_server(corenlp_path, corenlp_ver):

    java_home = os.getenv("JAVA_HOME", None)
    if java_home is None:
        javac_cmd = "javac"
    else:
        javac_cmd = os.path.join(java_home, "bin", "javac")

    path = os.path.dirname(os.path.realpath(__file__))
    file, pathname, description = \
        imp.find_module('util', [os.path.join(path, 'corenlp')])
    
    util = imp.load_module('util', file, pathname, description)
    file.close()
    
    classpath = util.validate_jars(corenlp_path, corenlp_ver)
    classpath += ":" + os.path.join(
        path, "corenlp", "jars", "netty-all-4.0.25.Final.jar")

    src = os.path.join(
        path, u"server-src", "edu", "columbia", "cs", "nlp", u"*.java")
    bin = os.path.join(
        path, u"server-bin", "edu", "columbia", "cs", "nlp", u"*.class")
    jar = os.path.join(path, "corenlp", "jars", "cnlpserver.jar")

    bin_dir = os.path.join(path, "server-bin")
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)

    server_cla = os.path.join(
        bin_dir, u"edu", u"columbia", u"cs", u"nlp", u"CoreNLPServer.class")
    handler_cla = os.path.join(
        bin_dir, u"edu", u"columbia", u"cs", u"nlp", 
        u"CoreNLPServerHandler.class")
    init_cla = os.path.join(
        bin_dir, u"edu", u"columbia", u"cs", u"nlp", 
        u"CoreNLPServerInitializer.class")

    os.system('{} -cp {} -d {} {}'.format(
        javac_cmd, classpath, bin_dir, src))

    if not os.path.exists(server_cla) or not os.path.exists(handler_cla) \
        or not os.path.exists(init_cla):
        print "Failed to build java server."
        sys.exit(1)
    
    server_cla = os.path.join(
        u"edu", u"columbia", u"cs", u"nlp", u"CoreNLPServer.class")
    handler_cla = os.path.join(
        u"edu", u"columbia", u"cs", u"nlp", 
        u"CoreNLPServerHandler.class")
    init_cla = os.path.join(
        u"edu", u"columbia", u"cs", u"nlp", 
        u"CoreNLPServerInitializer.class")

    bin_list = " ".join([server_cla, handler_cla, init_cla])
    print bin_list

    os.system('cd {}; jar cf {} {}'.format(bin_dir, jar, bin_list))
    if not os.path.exists(jar):
        print "Failed to package server in jar file."
        sys.exit(1)

    shutil.rmtree(bin_dir)

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
        'corenlp': [os.path.join('jars', 'cnlpserver.jar'),
                    os.path.join('jars', "netty-all-4.0.25.Final.jar"),]},

)
                    
