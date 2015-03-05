import os

class MissingJavaLibException(Exception):
    pass

def validate_jars(path, ver):

    ejml = u'ejml-0.23.jar'
    joda = u'joda-time.jar'
    jollyday = u'jollyday.jar'
    cnlp = u'stanford-corenlp-{}.jar'.format(ver)
    models = u'stanford-corenlp-{}-models.jar'.format(ver)
    xom = u'xom.jar'
    
    jars = [ejml, joda, jollyday, cnlp, models, xom]

    for jar in jars:
        jar_path = os.path.join(path, jar)
        if not os.path.exists(jar_path):
            raise MissingJavaLibException(
                u'Cannot find jar file {} in {}\n'.format(path, jar))

    return u':'.join([os.path.join(path, jar) for jar in jars])
