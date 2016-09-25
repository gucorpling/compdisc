import numpy
import os
from scipy.spatial.distance import cosine

from scoring import find_boundaries, smoothing, depth_scoring, boundarize, window_diff
from tile_reader import TileReader

options = {'vocab_tags': ["NOUN", "PROPN"],
           'block_length': 3,
           'smoothing_window': 2,
           'smoothing_type': 'liberal',  # liberal or conservative
           'out_type': 0}  # 0 or 1


def _vectorize(block, options):
    """
    creates a vector representation of a block
    :param block:
    :return: numpy.array
    """
    vector = numpy.zeros(300)
    for sentence in block:
        for token in sentence:
            vector += token.vector
    return vector


def tile(filename, options=options):
    filename = os.getcwd() + "\\" + filename
    reader = TileReader()
    reader.read(filename)
    reader.set_vocab_tags(options['vocab_tags'])
    blocks = reader.get_blocks(options['block_length'])
    print(len(reader.sentences))

    # placeholder for similarity scores
    similarity_scores = []

    for blockA, blockB in blocks:
        vecA = _vectorize(blockA, options)
        vecB = _vectorize(blockB, options)
        similarity_scores.append(cosine(vecA, vecB))

    bounds_1 = find_boundaries(similarity_scores, options['smoothing_window'], options['smoothing_type'])
    bounds_2 = boundarize(depth_scoring(similarity_scores), options['smoothing_type'])
    bounds = bounds_2

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
        out_list = [1]
        for i in xrange(len(reader.sentences)):
            if i in bounds:
                out_list.append(1)
            else:
                out_list.append(0)
        return out_list

city = 'merida'

segments = tile('data\\GUM_voyage_'+city+'_noheads.txt', options)

golds = {}
with open(os.getcwd() + "\\data\\boundaries") as infile:
    for line in infile:
        line = line.split()
        golds[line[0]] = [int(x) for x in line[1:]]
print 'predicted:   ', segments
print 'gold:        ', golds[city]

print window_diff(segments, golds[city], 3)
