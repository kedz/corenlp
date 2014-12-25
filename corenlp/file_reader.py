from .document import *
import os
import tarfile    
import xml.etree.cElementTree as ET

__brackets = {
    u'-LRB-': u'(',
    u'-lrb-': u'(',
    u'-RRB-': u')',
    u'-rrb-': u')',
    u'-LCB-': u'{',
    u'-lcb-': u'{',
    u'-RCB-': u'}',
    u'-rcb-': u'}',
    u'-LSB-': u'[',
    u'-lsb-': u'[',
    u'-RSB-': u']',
    u'-rsb-': u']'}


def open_dir(path, dep_type=u'collapsed-ccprocessed-dependencies'):
    for fname in os.listdir(path):
        if fname.endswith(u'.xml'):
            yield read_xml(os.path.join(path, fname), dep_type=dep_type)
        elif fname.endswith(u'.tar.gz') or fname.endswith(u'.tgz'):
            fpath = os.path.join(path, fname)
            for doc in open_tar_gz(fpath, dep_type=dep_type):
                yield doc


def read_xml(path, dep_type=u'collapsed-ccprocessed-dependencies'):
    return _parse_source(path, dep_type=dep_type)

def open_tar_gz(path, dep_type=u'collapsed-ccprocessed-dependencies'):
    tar = tarfile.open(mode="r:gz", fileobj=file(path))
    for member in tar:
        yield _parse_source(tar.extractfile(member))

def _parse_source(source, dep_type=u'collapsed-ccprocessed-dependencies'):

    # Temporary vars for token level attributes.
    _word = None
    _lemma = None
    _pos = None
    _ner = None
    _char_offset_begin = None
    _char_offset_end = None
    _token_idx = 0
    _sent_idx = 0

    # Temporary vars for sentence level attributes.
    _parse = None
    _deps = None
    _tokens = []
    _gov2deps = None
    _dep2govs = None
    _governor = None
    _dependent = None

    sents = []

    _not_in_coref = True
#    _coref_start = None
#    _coref_end = None
#    _coref_head = None
#    _coref_sentence = None
#    _mentions = []
#    _mention_chains = []


    for event, elem in ET.iterparse(source, events=('start', 'end')):
        if event == u'start':
            if elem.tag == 'dependencies':
                if dep_type == elem.attrib['type']:
                    _gov2deps = {}
                    _dep2govs = {}
        else:
            if elem.tag == 'word':
                if isinstance(elem.text, str):
                    _word = elem.text.decode(u'utf-8')               
                else:
                    _word = elem.text
                _word = __brackets.get(_word, _word)
            elif elem.tag == 'lemma':
                if isinstance(elem.text, str):
                    _lemma = elem.text.decode(u'utf-8')    
                else:
                    _lemma = elem.text
            elif elem.tag == 'POS':
                if isinstance(elem.text, str):
                    _pos = elem.text.decode(u'utf-8')
                else:
                    _pos = elem.text
            elif elem.tag == 'NER':
                _ner = elem.text.decode(u'utf-8')
#            elif elem.tag == 'CharacterOffsetBegin':
#                _char_offset_begin = int(elem.text)
#            elif elem.tag == 'CharacterOffsetEnd':
#                _char_offset_end = int(elem.text)
            elif elem.tag == 'token':
            #    if _word == '``' or _word == '\'\'': 
#                    if _char_offset_end - _char_offset_begin == 1:
#                        _word = '"'
#
                _tokens.append(
                    Token(_word, _lemma, _pos, _ner, _token_idx, _sent_idx)) 
#                                     _char_offset_begin, _char_offset_end,
#
                _word = None
                _lemma = None
                _pos = None
                _ner = None
#                _char_offset_begin = None
#                _char_offset_end = None
                _token_idx += 1
#
#            # Recover Parse Tree here.
#            elif elem.tag == 'parse' and use_parse:
#                _parse = nltk.tree.Tree(unicode(elem.text))
#
#            # Recover dependencies here.
            elif elem.tag == 'governor' and _gov2deps is not None:
                idx = int(elem.attrib['idx']) - 1
                if idx > -1:
                    _governor = _tokens[idx]
                else:
                    _governor = Token('ROOT', 'root', 'ROOT', None, -1, _sent_idx)
            elif elem.tag == 'dependent' and _gov2deps is not None:
                idx = int(elem.attrib['idx']) - 1
                if idx > -1:
                    _dependent = _tokens[idx]
            elif elem.tag == 'dep' and _gov2deps is not None:
                rel = elem.attrib['type'].decode(u'utf-8')
                if _governor not in _gov2deps:
                    _gov2deps[_governor] = set()
                _gov2deps[_governor].add((rel, _dependent))
                if _dependent not in _dep2govs:
                    _dep2govs[_dependent] = set()
                _dep2govs[_dependent].add((rel, _governor))
                
#            # Recover coref chain here.
#            elif elem.tag == 'start' and use_coref:
#                _coref_start = int(elem.text) - 1
#            elif elem.tag == 'end' and use_coref:
#                _coref_end = int(elem.text) - 1
#            elif elem.tag == 'head' and use_coref:
#                _coref_head = int(elem.text) - 1
#            elif elem.tag == 'mention' and use_coref:
#                _mentions.append(Mention(_coref_start, _coref_end,
#                                         _coref_head, _coref_sentence))
#
#            elif elem.tag == 'coreference' and use_coref:
#                if len(_mentions) > 0:
#                    _mention_chains.append(_mentions)
#                _mentions = []
#
            elif elem.tag == 'sentence':
                if _not_in_coref:
#                    
#                    sentiment = None
#                    sentiment_val = None
#                    if 'sentiment' in elem.attrib:
#                        sentiment = elem.attrib['sentiment']
#                    if 'sentimentValue' in elem.attrib:
#                        sentiment_val = float(elem.attrib['sentimentValue'])
#                    
                    sents.append(Sentence(_tokens, _gov2deps, _dep2govs, _sent_idx))#  , _parse,
#                                          _basic_deps, _collapsed_deps,
#                                          _collapsed_ccproc_deps, _sent_idx,
#                                          sentiment, sentiment_val))
                    _tokens = []
#                    _parse = None
                    _dep2govs = None
                    _gov2deps = None
                    _current_deps = None
                    _token_idx = 0
                    _sent_idx += 1
#
#                else:
#                    _coref_sentence = int(elem.text) - 1
#
            elif elem.tag == 'sentences':
                _not_in_coref = False
#
#    return sents, _mention_chains
    return Document(sents)
