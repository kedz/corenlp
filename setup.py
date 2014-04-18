from setuptools import setup

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
    ]

)
                    
