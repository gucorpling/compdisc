import numpy
from xrenner.modules.xrenner_xrenner import Xrenner
from compdisc.vectors import Vectors

def bridging(xrenner, vectors, type='conservative'):
    """
    This is my bridging function. It takes an Xrenner object and a Vectors object and adds bridging coref
    to the Xrenner object. It has one option: 'conservative' or 'liberal' this determines whether the threshold
    for determining conference is the mean cosine distance of previous markables - 2 * the standard deviation
    (conservative), or the mean cosine distance of previous markables - the standard deviation (liberal).
    :param xrenner: an xrenner object
    :param vectors: a vectors object
    :param type: 'conservative' or 'liberal'
    :return: None
    """
    markable_vectors = []
    for markable in xrenner.markables:
        markable_vectors.append(vectors.get(markable.text, False))

    for i in range(len(xrenner.markables)):
        if not (xrenner.markables[i].antecedent == 'none' and
                        xrenner.markables[i].form == 'common' and
                        xrenner.markables[i].definiteness == 'def'):
            continue

        distances = []
        for j in range(i):
            distances.append(vectors.distance(markable_vectors[i], markable_vectors[j]))

        temp = numpy.array([distance for distance in distances if not numpy.isnan(distance)])

        min_distance = temp.min()

        if type is 'conservative':
            threshold = temp.mean() - (2 * temp.std())
        else:
            threshold = temp.mean() - temp.std()

        if min_distance <= threshold:
            xrenner.markables[i].antecedent = xrenner.markables[distances.index(min_distance)]
            xrenner.markables[i].coref_type = 'bridge'

    return None

if __name__ == "__main__":

    xrenner = Xrenner(override='GUM')
    xrenner.analyze('clinton_example.conll10', 'conll')

    vecs = Vectors('../vectors/GoogleNewsVecs.txt', False)

    bridging(xrenner, vecs)

    for markable in xrenner.markables:
        print(markable.text, markable.antecedent, markable.coref_type)
