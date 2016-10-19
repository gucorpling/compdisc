import numpy
import cPickle
from sklearn.neighbors import BallTree
from scipy.spatial.distance import cosine


class Vectors:
    def __init__(self, filename=None, optimize=True):
        self.word_index = {}
        self.vectors = []
        self.words = []
        self.ball_tree = None
        if filename:
            with open(filename) as infile:
                print('Reading vectors...')
                index = 0
                for line in infile:
                    line = line.split()
                    if len(line) == 301:
                        self.word_index[line[0]] = index
                        self.vectors.append([float(x) for x in line[1:]])
                        self.words.append(line[0])
                        index += 1
                print('Finished')
        if optimize and filename:
            self.optimize()

    def optimize(self):
        if not self.ball_tree:
            print('Optimizing search...')
            self.ball_tree = BallTree(self.vectors, metric=cosine)
            print('Finished.')
        else:
            print('Already optimized.')

    def save(self, filename):
        if filename.split('.')[-1] != 'vecs':
            filename += '.vecs'
        with open(filename, 'wb') as outfile:
            cPickle.dump((self.word_index,
                          self.vectors,
                          self.words,
                          self.ball_tree),
                         outfile)
        print('saved as '+filename)

    def load(self, filename):
        if filename.split('.')[-1] != 'vecs':
            filename += '.vecs'
        with open(filename, 'rb') as infile:
            self.word_index, self.vectors, self.words, self.ball_tree = cPickle.load(infile)

    def get(self, string, errors=True):
        # type: (str, bool) -> list
        return_vec = [0]*len(self.vectors[0])
        for word in string.split():
            try:
                return_vec = numpy.add(self.vectors[self.word_index[word]],return_vec)
            except Exception as e:
                if errors:
                    raise e
        return return_vec

    def search(self, vector, k=1, return_distance=False):
        if self.ball_tree:
            a = self.ball_tree.query(numpy.array(vector).reshape(1, -1), k=k)
            dist, ind = a[0][0], a[1][0]
        else:
            dists = [cosine(vector, vec) for vec in self.vectors]
            ind = numpy.argsort(dists)[:k]
            dist = [dists[i] for i in ind]
            del dists
        if return_distance:
            return tuple(((self.words[ind[i]], dist[i]) for i in xrange(len(ind))))
        else:
            return tuple(self.words[ind[i]] for i in xrange(len(ind)))

    def distance(self, item1, item2, errors=True):
        if isinstance(item1, str):
            item1 = self.get(item1, errors=errors)
        if isinstance(item2, str):
            item2 = self.get(item2, errors=errors)
        return cosine(item1, item2)