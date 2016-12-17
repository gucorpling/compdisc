import numpy
import pickle
from sklearn.neighbors import BallTree
from scipy.spatial.distance import cosine
from sklearn.svm import LinearSVC


class Vectors:
    def __init__(self, filename=None, optimize=True):
        self.word_index = {}
        self.vectors = []
        self.words = []
        self.ball_tree = None
        if filename:
            with open(filename, encoding='utf-8') as infile:
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
            pickle.dump((self.word_index,
                          self.vectors,
                          self.words,
                          self.ball_tree),
                         outfile)
        print('saved as '+filename)

    def load(self, filename):
        if filename.split('.')[-1] != 'vecs':
            filename += '.vecs'
        with open(filename, 'rb') as infile:
            self.word_index, self.vectors, self.words, self.ball_tree = pickle.load(infile)

    def get(self, string, errors=True):
        # type: (str, bool) -> list
        return_vec = [0]*len(self.vectors[0])
        for word in string.split():
            try:
                return_vec = numpy.add(self.vectors[self.word_index[word]], return_vec)
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
            return tuple(((self.words[ind[i]], dist[i]) for i in range(len(ind))))
        else:
            return tuple(self.words[ind[i]] for i in range(len(ind)))

    def distance(self, item1, item2, errors=True):
        if isinstance(item1, str):
            item1 = self.get(item1, errors=errors)
        if isinstance(item2, str):
            item2 = self.get(item2, errors=errors)
        return cosine(item1, item2)

class RelationLabeler:
    def __init__(self, vector_file):
        self.sent_types = ['decl', 'frag', 'sub', 'ger', 'intj', 'inf', 'wh', 'other', 'imp', 'q']
        self.relations = ['purpose_r',
                          'antithesis_r',
                          'cause_r',
                          'concession_r',
                          'evidence_r',
                          'joint_m',
                          'circumstance_r',
                          'preparation_r',
                          'elaboration_r',
                          'span',
                          'condition_r',
                          'restatement_r',
                          'evaluation_r',
                          'background_r',
                          'result_r',
                          'motivation_r',
                          'restatement_m',
                          'joint_r',
                          'solutionhood_r',
                          'contrast_m',
                          'sequence_m',
                          'justify_r',
                          'ROOT']

        self.vectors = Vectors(vector_file, False)
        self.classifier = LinearSVC()

    def train(self, filename):
        X = []
        Y = []
        for example, label in self.get_data(filename):
            X.append(example)
            Y.append(label)
        self.classifier.fit(X, Y)

    def test(self, filename):
        correct, incorrect = 0, 0
        for example, label in self.get_data(filename):
            prediction = self.classifier.predict(example)
            if prediction == label:
                correct += 1
            else:
                incorrect += 1
            #print(self.classifier.predict(example), label)
        print('accuracy: ', correct/(correct+incorrect))

    def get_data(self, filename):
        for tree in self.rst_loader(filename):
            for i in range(len(tree)):
                current_line = tree[i+1]
                if int(current_line[5]) not in tree:
                    continue
                parent = tree[int(current_line[5])]
                example = []

                # add data from rst parse to example
                current_sent_type = [0]*10
                current_sent_type[self.sent_types.index(current_line[1])] = 1
                example.extend(current_sent_type)

                parent_sent_type = [0]*10
                parent_sent_type[self.sent_types.index(parent[1])] = 1
                example.extend(parent_sent_type)

                if current_line[2] == 'head':
                    example.append(1)
                else:
                    example.append(0)

                if parent[2] == 'head':
                    example.append(1)
                else:
                    example.append(0)

                if current_line[3] == 'caption':
                    example.append(1)
                else:
                    example.append(0)

                if parent[3] == 'caption':
                    example.append(1)
                else:
                    example.append(0)

                if current_line[4] == 'ordered':
                    example.extend([1,0])
                elif current_line[4] == 'unordered':
                    example.extend([0,0])
                else:
                    example.extend([0,0])

                if parent[4] == 'ordered':
                    example.extend([1,0])
                elif parent[4] == 'unordered':
                    example.extend([0,0])
                else:
                    example.extend([0,0])

                if current_line[7] == 'date':
                    example.append(1)
                else:
                    example.append(0)

                if parent[7] == 'date':
                    example.append(1)
                else:
                    example.append(0)

                # add length data
                # distance in rst tree
                example.append(int(current_line[5])-i+1)
                # length of the current line
                example.append(len(current_line[8]))
                # length of the parent
                example.append(len(parent[8]))
                # difference in length of lines
                example.append(len(parent[8])-len(current_line[8]))

                # vector space difference between the root, nsubj, and dobj
                current_root, current_subj, current_obj = None, None, None
                current_sent = ''
                for word in current_line[8].items():
                    word = word[1]
                    if word[6] == 'root':
                        current_root = word[1]
                    elif word[6] == 'nsubj' and current_subj is None:
                        current_subj = word[1]
                    elif word[6] == 'dobj' and current_obj is None:
                        current_obj = word[1]
                    current_sent += word[1] + ' '

                parent_root, parent_subj, parent_obj = None, None, None
                parent_sent = ''
                for word in parent[8].items():
                    word = word[1]
                    if word[6] == 'root':
                        parent_root = word[1]
                    elif word[6] == 'nsubj' and parent_subj is None:
                        parent_subj = word[1]
                    elif word[6] == 'dobj' and parent_obj is None:
                        parent_obj = word[1]
                    parent_sent += word[1]+' '

                if parent_root is not None and current_root is not None:
                    try:
                        example.append(self.vectors.distance(parent_root, current_root))
                    except Exception:
                        example.append(1)
                else:
                    example.append(1)

                if parent_subj is not None and current_subj is not None:
                    try:
                        example.append(self.vectors.distance(parent_subj, current_subj))
                    except Exception:
                        example.append(1)
                else:
                    example.append(1)

                if parent_obj is not None and current_obj is not None:
                    try:
                        example.append(self.vectors.distance(parent_obj, current_obj))
                    except Exception:
                        example.append(1)
                else:
                    example.append(1)
                try:
                    example.append(self.vectors.distance(parent_sent, current_sent))
                except Exception:
                    example.append(1)

                yield example, self.relations.index(current_line[6])

    @staticmethod
    def rst_loader(filename):
        with open(filename, encoding='utf-8') as infile:
            data = {}
            for line in infile:
                if line== '\n':
                    return_data = data
                    data = {}
                    yield return_data
                else:
                    line = line.split()
                    parse = {}
                    parse_section = line[9].split('///')
                    for entry in parse_section:
                        entry = entry.split('|||')
                        parse[int(entry[0])] = entry[1:]
                    value = line[1:9]
                    value.append(parse)
                    data[int(line[0])] = value


rl = RelationLabeler('../vectors/GoogleNewsVecs.txt')
rl.train('rst_train.rsd')
rl.test('rst_test.rsd')
