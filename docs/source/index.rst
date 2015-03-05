.. corenlp documentation master file, created by
   sphinx-quickstart on Thu Mar  5 14:19:10 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Python CoreNLP Wrapper
======================

The Python CoreNLP Wrapper is exactly that -- a convenient interface
to the Stanford CoreNLP library. It's main goal is to help you avoid writing
Java and let you focus on doing actual NLP.

Installation
^^^^^^^^^^^^

You will need a Java/Javac version >= 1.7 and Stanford CoreNLP 
version >= 3.5.1. Older versions of CoreNLP will probably work but I have not
tested them. In order for the wrapper to install the following environment
variables need to be set:
::
    
    export CORENLP_DIR=path/to/corenlp-jars
    export CORENLP_VER=Major.Minor.Patch
    
For example on my system I have
::
    
    export CORENLP_DIR=/home/kedz/javalibs/stanford-corenlp-full-2015-01-30
    export CORENLP_VER=3.5.1
     
Optionally, you can specify the Java version you would like to use by
setting the JAVA_HOME environment variable.

Once those variables are set, the easiest way to install is with pip.
::
    
    pip install corenlp
    
Quick Start
^^^^^^^^^^^

To begin, simply start the CoreNLP server. 
::
    
    import corenlp.server
    corenlp.server.start()


Now create a CoreNLPClient and begin annotating:
::

    import corenlp.client
    client = corenlp.client.CoreNLPClient()
    
    doc = client.annotate(u"Hello, world!")
    print doc

::
    
    >> Hello , world !


When done, you can stop server as well. Unless explicitly stopped, the 
server will be available after the current python script has finished.

::
    
    corenlp.server.stop()
    

By default, :code:`annotate` returns a :code:`Document` which in turn
contains :code:`Sentence` objects and :code:`Token` objects.

::
    
    for sent in doc:
        for token in sent:
            print token.lem,

::
    
    >> hello , world !
    
Alternatively, you can get the raw XML output as a unicode object:
::
    
    xml = client.annotate(u"Hello, world!", return_xml=True)
    print xml

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <?xml-stylesheet href="CoreNLP-to-HTML.xsl" type="text/xsl"?>
    <root>
    <document>
        <sentences>
        <sentence id="1">
            <tokens>
            <token id="1">
                <word>Hello</word>
                <lemma>hello</lemma>
                <CharacterOffsetBegin>0</CharacterOffsetBegin>
                <CharacterOffsetEnd>5</CharacterOffsetEnd>
                <POS>UH</POS>
            </token>
    ...
    </root> 

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

