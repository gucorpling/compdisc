import numpy
import os
from scipy.spatial.distance import cosine
from vectors import Vectors

from scoring import find_boundaries, smoothing, depth_scoring, boundarize, window_diff
from tile_reader import TileReader

options = {'vocab_tags': ["NOUN", "PROPN"],
           'block_length': 3,
           'smoothing_window': None,  # int or None
           'smoothing_type': 'liberal',  # liberal or conservative
           'out_type': 0,  # 0 or 1
           'vectors': None} # None or a Vectors object (None defaults to Levy & Goldberg 2014)


def _vectorize(block, vectors):
    """
    creates a vector representation of a block
    :param block:
    :return: numpy.array
    """
    if vectors is None:
        vector = numpy.zeros(300)
        for sentence in block:
            for token in sentence:
                vector += token.vector
        return vector
    else:
        vector = numpy.zeros(300)
        for sentence in block:
            for token in sentence:
                vector += numpy.array(vectors.get(str(token), False))
        return vector


def tile(filename, options=options):
    filename = os.getcwd() + "\\" + filename
    reader = TileReader()
    reader.read(filename, newline_tokenization=True)
    reader.set_vocab_tags(options['vocab_tags'])
    blocks = reader.get_blocks(options['block_length'])

    # placeholder for similarity scores
    similarity_scores = []

    for blockA, blockB in blocks:
        vecA = _vectorize(blockA, options['vectors'])
        vecB = _vectorize(blockB, options['vectors'])
        similarity_scores.append(cosine(vecA, vecB))

    if options['smoothing_window'] is None:
        bounds = boundarize(depth_scoring(similarity_scores), options['smoothing_type'])
    else:
        bounds = find_boundaries(similarity_scores, options['smoothing_window'], options['smoothing_type'])

    if options['out_type'] == 1:
        out_string = ''
        count = 0
        for sent in reader.sentences:
            if count in bounds:
                out_string += "\n-----\n"
            out_string += sent.text + '\n'
            count += 1
        return out_string
    else:
        out_list = []
        for i in xrange(len(reader.sentences)):
            if i-(options['block_length']) in bounds:
                out_list.append(1)
            else:
                out_list.append(0)
        out_list[0] = 1
        return out_list

city = 'chatham'

#options['vectors'] = Vectors('vectors\GoogleNewsVecs.txt', False)

segments = tile('data\\GUM_voyage_'+city+'_noheads.txt', options)
print segments

golds = {}
with open(os.getcwd() + "\\data\\boundaries") as infile:
    for line in infile:
        line = line.split()
        golds[line[0]] = [int(x) for x in line[1:]]
print 'predicted:   ', segments, len(segments)
print 'gold:        ', golds[city], len(golds[city])

print window_diff(segments, golds[city], 3)
