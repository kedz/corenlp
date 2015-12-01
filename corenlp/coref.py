
class Mention(object):
    def __init__(self, start, end, head, sentence, text):
        self.start = start
        self.end = end
        self.head = head
        self.sentence = sentence
        self.text = text

    def __str__(self):
        return str((self.start, self.end, self.head, self.sentence, 
            self.text.encode("utf8")))
   
class CorefChain(object):
    def __init__(self, mentions):
        self.mentions = mentions
        self.rep_mention = self.mentions[0]

    def __len__(self):
        return len(self.mentions)

    def __str__(self):
        return "{} ({} mentions)".format(
            self.rep_mention.text, len(self.mentions))

    def __iter__(self):
        return iter(self.mentions)

