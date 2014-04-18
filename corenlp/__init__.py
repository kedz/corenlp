import xml.etree.cElementTree as ET
import nltk
from collections import defaultdict

class Document:
    def __init__(self, xmlfile, pos=True, lemma=True, ner=True, parse=True,
                 coref=True, basic_deps=False, coll_deps=False,
                 coll_ccp_deps=True, verbose=False):

        sents, coref_chains = _parse_source(xmlfile, use_pos=pos,
                                            use_lemma=lemma, use_ner=ner,
                                            use_parse=parse, use_coref=coref,
                                            use_basic_deps=basic_deps,
                                            use_coll_deps=coll_deps,
                                            use_coll_ccp_deps=coll_ccp_deps,
                                            verbose=verbose)
        self.sents = sents
        self.coref_map = self._build_coref_map(coref_chains)
        self.mention_chains = set(self.coref_map.values())

    def rep_head(self, token):
        """
        Get the representative mention head token for token.
        If token is not part of a mention chain, then return the
        token.

        token -- A Token object.
        """
        mention_chain = self.coref_map.get(token, None)
        if mention_chain is None:
            return token
        else:
            return mention_chain.rep_head
    
    def mention_chain(self, token):
        """
        Return the corresponding mention chain for a token. If token
        is not part of a mention chain, return None.

        token - A Token object.
        """
        return self.coref_map.get(token, None)

    def _build_coref_map(self, coref_chains):
        coref_map = {}
        for chain in coref_chains:
            entity = MentionChain(chain, self)
            for mention in chain:
                sent = mention.sent
                start = mention.start
                end = mention.end
                for token in self[sent][start:end]:
                    coref_map[token] = entity 
        return coref_map

    def __len__(self):
        return len(self.sents)

    def __getitem__(self, index):
        return self.sents[index]

    def mention_string(self, mention):
        tokens = []
        sent = mention.sent
        start = mention.start
        end = mention.end
        for t in self.sents[sent].tokens[start:end]:
            tokens.append(t._surface)
        return u' '.join(tokens)

    def __str__(self):
        return u'\n'.join([unicode(s) for s in self.sents])        

class Sentence:
    def __init__(self, tokens, parse,
                 basic_deps, collapsed_deps, collapsed_ccproc_deps, idx,
                 sentiment, sentiment_value):
        self.tokens = tuple(tokens)
        self.parse = parse
        self.basic_deps = basic_deps
        self.coll_deps = collapsed_deps
        self.coll_ccp_deps = collapsed_ccproc_deps
        if collapsed_ccproc_deps is not None:
            self.deps = collapsed_ccproc_deps
        elif collapsed_deps is not None:
            self.deps = collapsed_deps
        elif basic_deps is not None:
            self.deps = basic_deps
        else:
            self.deps = None
        self._dgraph = None
        self.idx = idx
        self.sentiment = sentiment
        self.sentiment_value = sentiment_value

    def __getitem__(self, index):
        return self.tokens[index]

    def __str__(self):
        tokstrings = []
        prev_offset = self[0].char_offset_begin
        for t in self.tokens:
            space = u' ' * (t.char_offset_begin - prev_offset)
            tokstrings.append(unicode(space))
            tokstrings.append(t._surface)
            prev_offset = t.char_offset_end
        return u''.join(tokstrings)

    def __repr__(self):
        return u'Sentence ({}) {}'.format(self.idx, unicode(self))
    
    def pos_str(self):
        tokstrs = [u'{}/{}'.format(t._surface, t.pos) for t in self.tokens]
        return u' '.join(tokstrs)

    def dep_graph(self):
        if self.deps is None:
            return None
        if self._dgraph is None:
            self._dgraph = DependencyGraph(self.deps)
        return self._dgraph
      
#    def _attrs(self):
#        return (self.tokens, self.parse, self.basic_deps, self.coll_deps,
#                self.coll_ccp_deps, self.deps, self._dgraph, self.idx)

#    def __hash__(self):
#        return hash(self._attrs())

#    def __eq__(self, other):
#        if not isinstance(other, Sentence):
#            return False
#        else:
#            return self._attrs() == other._attrs()

class Token:
    def __init__(self, surface, lem, pos, ner,
                 char_offset_begin, char_offset_end, idx):
        self._surface = surface
        self.lem = lem
        self.pos = pos
        self.ne = ner
        self.idx = idx
        self.char_offset_begin = char_offset_begin
        self.char_offset_end = char_offset_end

    def __len__(self):
        return len(self._surface)

    def __str__(self):
        return self._surface

    def __repr__(self):
        return 'Token ({}) {}'.format(self.idx, self._surface)


class TypedDependency:
    def __init__(self, dep, gov, deptype):
        self.dep = dep
        self.gov = gov
        self.type = deptype

    def __str__(self):
        return '({}::{}::{})'.format(self.dep, self.type, self.gov)

    def __repr__(self):
        return '(Dep:{} {} :: Type: {} :: Gov: {} {})'.format(self.dep.idx,
                                                              self.dep,
                                                              self.type,
                                                              self.gov.idx,
                                                              self.gov)


class DependencyGraph:
    def __init__(self, dep_list):
        self._list = dep_list
        self.type = defaultdict(list)
        self.govs = defaultdict(list)
        self.deps = defaultdict(list)
        for rel in dep_list:
            self.type[rel.type].append(rel)
            self.govs[rel.gov].append(rel)
            self.deps[rel.dep].append(rel)

    def __getitem__(self, index):
        return self._list[index]

    def to_ipython(self):
        import pygraphviz as pgv
        from IPython.display import Image        
        G=pgv.AGraph()
                
        for rel in self:
            G.add_edge(unicode(rel.dep), unicode(rel.gov), label=rel.type)    
        
        G.layout(prog='dot')
        G.draw('/tmp/deptree.png')
        return Image(filename='/tmp/deptree.png')


class Mention:
    def __init__(self, span_start, span_end, head_idx, sent_idx):
        self.sent = sent_idx
        self.start = span_start
        self.end = span_end
        self.head = head_idx


    def __str__(self):
        return 'Mention(sent={}, start={}, head={}, end={})'.format(self.sent,
                                                                    self.start,
                                                                    self.head,
                                                                    self.end)

class MentionChain:
    def __init__(self, mention_chain, doc):
        mention_heads = []
        mention_tokens = []                
        for mention in mention_chain:
            s = mention.sent
            h = mention.head
            start = mention.start
            end = mention.end
            mention_heads.append(doc[s][h])
            mention_tokens.append(doc[s][start:end])
        self.rep_head = mention_heads[0]
        self.rep_tokens = mention_tokens[0]
        self.mention_heads = tuple(mention_heads)
        self.mention_tokens = tuple(mention_tokens)


def _parse_source(source, use_pos=True, use_lemma=True, use_ner=True,
                  use_parse=True, use_coref=True, use_basic_deps=False,
                  use_coll_deps=False, use_coll_ccp_deps=True, verbose=False):


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
    _basic_deps = None
    _collapsed_deps = None
    _collapsed_ccproc_deps = None
    _tokens = []
    _current_deps = None

    _governor = None
    _dependent = None

    sents = []

    _not_in_coref = True
    _coref_start = None
    _coref_end = None
    _coref_head = None
    _coref_sentence = None
    _mentions = []
    _mention_chains = []


    for event, elem in ET.iterparse(source, events=('start', 'end')):
        if event == 'start':
            if elem.tag == 'dependencies':
                dtype = elem.attrib['type']
                if dtype == 'collapsed-ccprocessed-dependencies':
                    if use_coll_ccp_deps:
                        _current_deps = _collapsed_ccproc_deps = []
                elif dtype == 'collapsed-dependencies':
                    if use_coll_deps:
                        _current_deps = _collapsed_deps = []
                elif dtype == 'basic-dependencies':
                    if use_basic_deps:
                        _current_deps = _basic_deps = []
                else:
                    _current_deps = None
        else:
            if elem.tag == 'word':
               _word = unicode(elem.text)
               if _word == u'-LRB-':
                   _word = u'('
               elif _word == u'-RRB-':
                   _word = u')'
               elif _word == u'-LCB-':
                   _word = u'{'
               elif _word == u'-RCB-':
                   _word = u'}'
               elif _word == u'-LSB-':
                   _word = u'['
               elif _word == u'-RSB-':
                   _word = u']'

            elif elem.tag == 'lemma' and use_lemma:
                _lemma = unicode(elem.text)
            elif elem.tag == 'POS' and use_pos:
                _pos = unicode(elem.text)
            elif elem.tag == 'NER' and use_ner:
                _ner = unicode(elem.text)
            elif elem.tag == 'CharacterOffsetBegin':
                _char_offset_begin = int(elem.text)
            elif elem.tag == 'CharacterOffsetEnd':
                _char_offset_end = int(elem.text)
            elif elem.tag == 'token':
                if _word == '``' or _word == '\'\'': 
                    if _char_offset_end - _char_offset_begin == 1:
                        _word = '"'

                _tokens.append(Token(_word, _lemma, _pos, _ner,
                                     _char_offset_begin, _char_offset_end,
                                     _token_idx))

                _word = None
                _lemma = None
                _pos = None
                _ner = None
                _char_offset_begin = None
                _char_offset_end = None
                _token_idx += 1

            # Recover Parse Tree here.
            elif elem.tag == 'parse' and use_parse:
                _parse = nltk.tree.Tree(unicode(elem.text))

            # Recover dependencies here.
            elif elem.tag == 'governor' and _current_deps is not None:
                idx = int(elem.attrib['idx']) - 1
                if idx > -1:
                    _governor = _tokens[idx]
                else:
                    _governor = Token('ROOT', 'root', 'ROOT', None,
                                      None, None, -1)
            elif elem.tag == 'dependent' and _current_deps is not None:
                idx = int(elem.attrib['idx']) - 1
                if idx > -1:
                    _dependent = _tokens[idx]
            elif elem.tag == 'dep' and _current_deps is not None:
                rel = unicode(elem.attrib['type'])
                typed_dep = TypedDependency(_dependent, _governor, rel)
                _current_deps.append(typed_dep)

            # Recover coref chain here.
            elif elem.tag == 'start' and use_coref:
                _coref_start = int(elem.text) - 1
            elif elem.tag == 'end' and use_coref:
                _coref_end = int(elem.text) - 1
            elif elem.tag == 'head' and use_coref:
                _coref_head = int(elem.text) - 1
            elif elem.tag == 'mention' and use_coref:
                _mentions.append(Mention(_coref_start, _coref_end,
                                         _coref_head, _coref_sentence))

            elif elem.tag == 'coreference' and use_coref:
                if len(_mentions) > 0:
                    _mention_chains.append(_mentions)
                _mentions = []

            elif elem.tag == 'sentence':
                if _not_in_coref:
                    
                    sentiment = None
                    sentiment_val = None
                    if 'sentiment' in elem.attrib:
                        sentiment = elem.attrib['sentiment']
                    if 'sentimentValue' in elem.attrib:
                        sentiment_val = float(elem.attrib['sentimentValue'])
                    
                    sents.append(Sentence(_tokens, _parse,
                                          _basic_deps, _collapsed_deps,
                                          _collapsed_ccproc_deps, _sent_idx,
                                          sentiment, sentiment_val))
                    _tokens = []
                    _parse = None
                    _basic_deps = None
                    _collapsed_deps = None
                    _collapsed_ccproc_deps = None
                    _current_deps = None
                    _token_idx = 0
                    _sent_idx += 1

                else:
                    _coref_sentence = int(elem.text) - 1

            elif elem.tag == 'sentences':
                _not_in_coref = False

    return sents, _mention_chains
