_ptb_noun_tags = set([u'NN', u'NNS', u'NNP', u'NNPS'])
_ptb_verb_tags = \
    set([u'VB', u'VBD', u'VBG', u'VBN', u'VBP', u'VBZ'])

class Document(object):
    def __init__(self, sents, coref_chains):
        self.sents = tuple(sents)
        self.coref_chains = coref_chains
        
    def __getitem__(self, index):
        return self.sents[index]

    def __len__(self):
        return len(self.sents)

    def __unicode__(self):
        return self.format_tokens() 
    
    def __str__(self):
        return unicode(self).encode(u'utf-8')

    def format_tokens(self, fmt=None, token_sep=u' ', sentence_sep=u'\n'):
        return sentence_sep.join(
                [s.format_tokens(fmt=fmt, token_sep=token_sep) 
                 for s in self.sents])


        
class Sentence(object):
    def __init__(self, tokens, gov2deps, dep2govs, sent_index, parse): 
        
        #deps, dep_type, sent_idx,
               #  sentiment, sentiment_value):
        self.tokens = tuple(tokens)
        self.gov2deps = gov2deps
        self.dep2govs = dep2govs
        self.parse = parse
#        self.deps = deps
#        self.dep_type = dep_type
#        self._dgraph = None
        self.index = sent_index
#        self.sentiment = sentiment
#        self.sentiment_value = sentiment_value

    def __getitem__(self, index):
        return self.tokens[index]

    def __unicode__(self):
        return u' '.join(unicode(token) for token in self.tokens)

    def __str__(self):
        return unicode(self).encode(u'utf-8')

    def __repr__(self):
        return str(self)

    def get_ne_spans(self):
        spans = []
        curr_ne = None
        curr_ne_type = None
        curr_ne_start = None

        for t, token in enumerate(self.tokens):
            if token.ne != "O":
                # start of new ne
                if curr_ne_type != token.ne:
                    
                    # curr_ne is not empty
                    if curr_ne is not None:
                        spans.append(
                            (curr_ne, 
                             curr_ne_type,
                             (curr_ne_start, t)))
                    curr_ne = unicode(token)
                    curr_ne_type= token.ne
                    curr_ne_start = t
                # append previous
                else:
                    curr_ne += u" " + unicode(token)
            elif curr_ne is not None:
                spans.append(
                    (curr_ne, 
                     curr_ne_type,
                     (curr_ne_start, t)))
                curr_ne = None
                curr_ne_type = None
                curr_ne_start = None
        if curr_ne is not None:
            spans.append(
                (curr_ne,
                 curr_ne_type,
                 (curr_ne_start, len(self.tokens))))
        return spans
#    def __str__(self):
#        tokstrings = []
#        prev_offset = self[0].char_offset_begin
#        for t in self.tokens:
#            space = u' ' * (t.char_offset_begin - prev_offset)
#            tokstrings.append(unicode(space))
#            tokstrings.append(t._surface)
#            prev_offset = t.char_offset_end
#        return u''.join(tokstrings)
#
#    def __repr__(self):
#        return u'Sentence ({}) {}'.format(self.idx, unicode(self))
#    
#    def pos_str(self):
#        tokstrs = [u'{}/{}'.format(t._surface, t.pos) for t in self.tokens]
#        return u' '.join(tokstrs)
#
#    def dep_graph(self):
#        if self.deps is None:
#            return None
#        if self._dgraph is None:
#            self._dgraph = DependencyGraph(self.deps)
#        return self._dgraph
#      
##    def _attrs(self):
##        return (self.tokens, self.parse, self.basic_deps, self.coll_deps,
##                self.coll_ccp_deps, self.deps, self._dgraph, self.idx)
#
##    def __hash__(self):
##        return hash(self._attrs())
#
##    def __eq__(self, other):
##        if not isinstance(other, Sentence):
##            return False
##        else:
##            return self._attrs() == other._attrs()

    def format_tokens(self, fmt=None, token_sep=u' '):
        if fmt is None:
            fmt = lambda t: unicode(t)
        return token_sep.join([fmt(t) for t in self.tokens]) 



class Token(object):
    def __init__(self, surface, lem, pos, ne, nne, token_index, sent_index):
#                 char_offset_begin, char_offset_end, idx):

        if isinstance(surface, str):
            surface = surface.decode('utf-8')
        self.surface = surface
        if isinstance(lem, str):
            lem = lem.decode('utf-8')
        self.lem = lem
        self.pos = pos
        self.ne = ne
        self.nne = nne
        self.index = token_index
        self.sent_index = sent_index
#        self.char_offset_begin = char_offset_begin
#        self.char_offset_end = char_offset_end
    def is_noun(self):
        return self.pos in _ptb_noun_tags

    def is_verb(self):
        return self.pos in _ptb_verb_tags

    def __len__(self):
        return len(self.surface)

    def __str__(self):
        return self.surface.encode(u'utf-8')

    def __unicode__(self):
        return self.surface

    def __repr__(self):
        return u'{}/{}/{}/{}'.format(
            self.surface, self.lem, self.pos, self.ne).encode('utf-8')
