import numpy
import cPickle
from sklearn.neighbors import BallTree
from scipy.spatial.distance import cosine


class Vectors:
    """
    This is a class for storing word vectors. It offers O(1) look up for the vector for a word and O(log n) nearest neighbour
    search when given a vector. It also provides cosine distance between two words.
    """
    def __init__(self, filename=None, optimize=True):
        """
        The constructor. takes a word vector file where eachline is a word and its vector e.g. happy 0.54 0.65 0.12 ...
        defaulty optemizes for fast nearest neighbour searches O(log n) if this is set to false these searches are O(n).
        Currently only accepts files with vector sixe 300 though this can be changed on line 28.
        """
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
                    if len(line) == 301:  # word + length of vectors
                        self.word_index[line[0]] = index
                        self.vectors.append([float(x) for x in line[1:]])
                        self.words.append(line[0])
                        index += 1
                print('Finished')
        if optimize and filename:
            self.optimize()

    def optimize(self):
        """
        This function optimizes the nearest neighbour search
        """
        if not self.ball_tree:
            print('Optimizing search...')
            self.ball_tree = BallTree(self.vectors, metric=cosine)
            print('Finished.')
        else:
            print('Already optimized.')

    def save(self, filename):
        """
        saves the vector object to a file for fast reloading
        """
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
        """
        Loads a previoulsy saved vector object
        """
        if filename.split('.')[-1] != 'vecs':
            filename += '.vecs'
        with open(filename, 'rb') as infile:
            self.word_index, self.vectors, self.words, self.ball_tree = cPickle.load(infile)

    def get(self, string, errors=True):
        """
        This function gets the vector for a string. if the string a a single word it returns that words vector otherwise,
        If it contains more than word it returns the unnormalized sum of the vectors for each word in the string.
        when errors is set to false returns a vector of 0s for any word not in vocabulary, when set to True throws an error
        for any out of vocabulary word.
        """
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
        """
        This function performs a K nearest neigbour search when given a vector.
        """
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
        """
        This functon returns the cosine distance between the words in two strings, or between two vectors.
        """
        if isinstance(item1, str):
            item1 = self.get(item1, errors=errors)
        if isinstance(item2, str):
            item2 = self.get(item2, errors=errors)
        return cosine(item1, item2)
