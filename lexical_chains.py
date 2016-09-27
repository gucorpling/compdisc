"""
lexical chain module for text tiling
"""

from tile_reader import TileReader
from scoring import boundarize, depth_scoring, window_diff


# ======================================================================================================================
# Main
# ======================================================================================================================
class LexicalChains(object):

    def __init__(self):
        self.sentences = []
        self.actives = {}
        self.gap_scores = []
        self.boundary_vector = []

    def analyze(self, sents, window=4, pos_filter=('PUNCT', 'SYM', 'SPACE', 'DET'), boundary_type='liberal'):
        """
        Set attributes
        :param sents: (list) spacy-analyzed sentences
        :param window: (int) distance threshold within which chains are considered active
        :param boundary_type: (str) 'liberal' or 'conservative' boundary scoring
        :param pos_filter: (tuple) spacy pos_ labels to exclude (i.e. a pos-based stoplist)
        :return: void
        """
        self.sentences = self._preproc(sents, pos_filter)
        self.actives = self._get_actives(self.sentences, window)
        self.gap_scores = [len(self.actives[k]) for k in self.actives.keys()]
        self.boundary_vector = self._get_boundaries(self.gap_scores, boundary_type)

    @staticmethod
    def _preproc(sentences, pos_filter):
        """
        Filters out stop POSs and lemmatizes sentences
        :param sentences: list of tokenized sentences in doc
        :param pos_filter: tuple of spacy pos_ labels to filter out
        :return: list
        """
        filtered = [[tok for tok in sent if tok.pos_ not in pos_filter] for sent in sentences]
        lemmatized = [[tok.lemma_ for tok in sent] for sent in filtered]
        return lemmatized

    @staticmethod
    def _get_actives(sents, window):
        """
        Get active lexical chains for each gap between sentences
        :param sents: list of tokenized sentences
        :param window: difference threshold over which lexical chains are considered active
        :return: dictionary containing active lexical chains for each sentence transition
        """
        # initialize active chains dictionary
        actives = {}
        for i in xrange(len(sents)-1):
            actives[i] = set()

        # loop over all sentences
        for sent in sents:
            # get index and unique tokens from current sentence
            i = sents.index(sent)
            uniques_i = set(sent)

            # loop over all sentences within dist thresh of current
            for diff in xrange(window, 0, -1):
                # back off diff when there are less sentences left than dist thresh
                while not i + diff < len(sents):
                    diff -= 1
                # find shared tokens between current sent[i] and sent[i+diff]
                n = i + diff
                uniques_n = set(sents[n])
                intersection = uniques_i.intersection(uniques_n)

                # add the intersections to all affected transitions between sent[i] and sent[i+diff]
                for k in list(xrange(diff)):
                    [actives[i+k].add(word) for word in intersection]

        return actives

    @staticmethod
    def _get_boundaries(scores, boundary_type):
        """
        Calculate boundaries from gap scores
        :param scores: list containing # of active chains across each sentence gap in doc
        :param boundary_type: string indicating 'liberal' or 'conservative' boundary scoring
        :return: list indicating which sentences in doc constitute beginnings of new topic tiles
        """
        d_scores = depth_scoring(scores)
        boundaries = boundarize(d_scores, type=boundary_type)
        boundary_vector = [1] + [0 if i not in boundaries else 1 for i in xrange(len(scores))]
        return boundary_vector


# ======================================================================================================================
# Test if invoked directly
# ======================================================================================================================
if __name__ == "__main__":
    from decimal import Decimal
    import matplotlib.pyplot as plt
    import sys
    import os

    # set doc
    try:
        doc = sys.argv[1]
    except IndexError:
        sys.exit("ERROR: Expected 1 arg, got {}\nUsage: (python) lexical_chains.py <docname> <docpath>".format(
            len(sys.argv)-1))

    # get doc path
    path = os.path.dirname(__file__)
    if doc in ('coron','athens','chatham','cuba','merida'):
        doc_path = os.path.join(path, os.path.join("data", "GUM_voyage_{}_noheads.txt".format(doc)))
    else:
        raise ValueError("unrecognized document: {}".format(doc))

    # get gold
    gold_file = os.path.join(path, os.path.join("data", "GUM_5_gold_tiles.txt"))
    with open(gold_file) as f:
        boundaries = [[int(x) for x in line.split(",")] for line in f.read().split()]
    texts = ["athens", "chatham", "coron", "cuba", "merida"]
    gold_dict = dict(zip(texts, boundaries))
    gold = gold_dict[doc]



    # Instantiate TileReader
    reader = TileReader()
    reader.read(doc_path, newline_tokenization=True)
    sents = reader.sentences

    # Instantiate Lexical Chains
    chains = LexicalChains()
    chains.analyze(sents)

    # compare gold and predicted boundaries
    print "GOLD: {}".format(gold)
    print "MINE: {}".format(chains.boundary_vector)

    # get window_diff
    window_size = len(gold)/4
    wdiff = window_diff(chains.boundary_vector, gold, window_size)
    print "Window Diff: {}".format(wdiff)

    # Plot scores
    scores = [0] + chains.gap_scores
    plt.plot([x for x in xrange(len(scores))], scores)
    for index, grp in enumerate(zip(gold, chains.boundary_vector)):
        if 1 == grp[0] == grp[1]:
            plt.axvline(x=index, color = 'green', linewidth='2.0')
        elif 1 == grp[0] != grp[1]:
            plt.axvline(x=index, color = 'red')
        elif 1 == grp[1] != grp[0]:
            plt.axvline(x=index, color = 'gray')
    ymin, ymax = plt.ylim()
    xmin, xmax = plt.xlim()
    wdiff_rounded = round(Decimal(wdiff), 3)
    plt.text(xmax-(xmax-xmin)/4,ymax+0.5, "window diff: {}".format(wdiff_rounded))
    plt.show()
