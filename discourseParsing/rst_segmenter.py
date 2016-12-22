import re

class Token:
    def __init__(self, tok_line):
        self.tok_line = tok_line
        splitline = tok_line.split('\t')
        self.id = int(splitline[0])
        self.text = splitline[1]
        self.pos = splitline[3]
        self.parent_id = int(splitline[6])
        self.func = splitline[7]
        self.children = []
        self.subtree = [self.id]

    def __repr__(self):
        return self.tok_line


class Edu:
    def __init__(self, toks, root_tok):
        self.toks = toks
        self.root_tok = root_tok
        self.root_func = root_tok.func

    def __repr__(self):
        cols = []
        first_tok = self.toks[0]
        root_tok = self.root_tok
        cols.append(first_tok.text)
        cols.append(root_tok.text)
        cols.append('_') # sentence type
        cols.append(first_tok.pos)
        cols.append('|'.join([str(len(self.toks)), self.root_func]))
        cols.append('_')
        cols.append('_')
        cols.append('_')
        repr_toks = []
        for tok in self.toks:
            tok_line = re.sub(r'\t', r'|||', tok.tok_line)
            repr_toks.append(tok_line)
        cols.append('///'.join(repr_toks))
        return '\t'.join(cols)


def is_continuous(subtree, toks):
    subtree.sort()
    for i in xrange(subtree[0], subtree[-1] + 1):
        if i not in subtree:
            if toks[i - 1] != 0:
                if toks[i-1].parent_id != 0:
                    return False
    return True


def has_subj(subtree, toks):
    for id in subtree:
        tok = toks[id-1]
        if tok.func == "nsubj" or tok.func == "nsubjpass":
            return True
    return False




def segment_sentence(sentence):
    lines = sentence.split('\n')
    toks = []
    for line in lines:
        if line[0] != '#':
            toks.append(Token(line))

    # determine subtree of each token
    for tok in toks:
        if tok.func == "root":
            root = tok
        current_tok = tok
        while current_tok.parent_id > 0:
            parent = toks[current_tok.parent_id-1]
            if current_tok.id not in parent.subtree:
                parent.subtree.append(tok.id)
            current_tok = parent

    # determine whether each token could be root of a new edu
    for tok in toks:
        if tok.func in ['advcl', 'vmod', 'parataxis', 'conj']:
            subtree = tok.subtree
            subtree.sort()

            # check whether subtree is a continuous chunk of the sentence, not counting punc
            if is_continuous(subtree, toks):
                if has_subj(subtree, toks):
                    if subtree[-1] == len(toks) - 1:
                        # split sentence
                        edu1 = toks[:subtree[0]-1]
                        EDU1 = Edu(edu1, root)
                        edu2 = toks[subtree[0]-1:]
                        EDU2 = Edu(edu2, tok)
                        return [EDU1, EDU2]
                    elif subtree[0] == 0:
                        edu1 = toks[:subtree[-1]]
                        EDU1 = Edu(edu1, tok)
                        edu2 = toks[subtree[-1]:]
                        EDU2 = Edu(edu2, root)
                        return [EDU1, EDU2]

    EDU = Edu(toks, root)
    return [EDU]


if __name__ == '__main__':
    infile = 'GUM_interview_ants.conll10'
    outfile = infile[:-8] + '_segmented.conll'
    with open(infile) as dep:
        sentences = dep.read().strip().split('\n\n')
        with open(outfile, 'w') as segmented:
            edu_counter = 1
            for sent in sentences:
                edus = segment_sentence(sent)
                for edu in edus:
                    segmented.write(str(edu_counter) + '\t' + str(edu) + '\n')
                    edu_counter += 1