import tile_reader as tr
import os
import scoring

options = {
    'w': 2,
    'vocab_tags': ["NOUN", "PROPN", "VERB", "ADJ"]
}

def tile(filename, options):
    reader = tr.TileReader()
    reader.read(filename)
    reader.set_vocab_tags(options['vocab_tags'])
    w = options['w']
    blocks = reader.get_blocks(w)

    terms_seen = []
    new_terms_by_sent = []
    window_start = 0
    scores = []

    for blockA, blockB in blocks:

        # make sure we have info on # new terms in each sentence in block
        sent_index = window_start
        for sent in blockA + blockB:
            if len(new_terms_by_sent) <= sent_index:
                new_terms = 0
                for tok in sent:
                    if tok.pos_ in reader.vocab_tags:
                        lemma = tok.lemma
                        if lemma not in terms_seen:
                            new_terms += 1
                            terms_seen.append(lemma)
                new_terms_by_sent.append(new_terms)
            sent_index += 1

        # calculate block score
        new_terms_in_window = sum(new_terms_by_sent[window_start:window_start+2*w])
        total_words_in_window = sum([len(sent) for sent in blockA + blockB])
        score = float(new_terms_in_window)/total_words_in_window
        scores.append(score)

        window_start += 1

    boundaries = scoring.find_boundaries(scores)
    output = [1] + (w-2)*[0]
    for i in xrange(len(scores)):
        if i in boundaries:
            output.append(1)
        else:
            output.append(0)
    output += w*[0]

    # for sentence in reader.sentences:
    #     print sentence
    print 'sentences in reader: ', len(reader.sentences)
    return output

# testing code below adapted from james's code in word_vecs.py

#for city in ['athens', 'chatham', 'coron', 'cuba', 'merida']:
for city in ['chatham', 'coron', 'cuba']:
    print city
    segments = tile('data' + os.sep + 'GUM_voyage_'+city+'_noheads.txt', options)

    golds = {}
    with open(os.getcwd() + os.sep + 'data' + os.sep + 'boundaries_alternate') as infile:
        for line in infile:
            line = line.split()
            golds[line[0]] = [int(x) for x in line[1:]]
    print 'sentences in predicted: ', len(segments)
    print 'sentences in gold:   ', len(golds[city])
    print 'predicted:   ', segments
    print 'gold:        ', golds[city]

    print scoring.window_diff(segments, golds[city], 3)



