import numpy
from scipy.signal import argrelextrema


def smoothing(scores, smoothing_window=2):
    """
    This function normalizes and then smooths the similarity scores. returns a new list. a lower score must indicate
    a greater similarity (I think!?)
    :param smoothing_window: int  # must be even
    :param scores: list
    :return: list
    """
    # normalize in a range of 0 to 1
    min_score = min(scores)
    max_score = max(scores)
    normalized_scores = []
    for score in scores:
        normalized_scores.append((score - min_score) / float((max_score - min_score)))

    # smooth
    smoothed_scores = []
    for i in xrange(len(normalized_scores)):
        window_scores = []
        for j in xrange(smoothing_window / 2):
            if i-(j+1) >= 0:  # take score from left
                window_scores.append(normalized_scores[i - (j + 1)])
            if i + (j+1) < len(normalized_scores):  # take score from right
                window_scores.append((normalized_scores[i + (j + 1)]))
        window_scores.append(normalized_scores[i])  # take score from this point

        smoothed_scores.append(sum(window_scores) / float(len(window_scores)))

    return smoothed_scores


def depth_scoring(scores):
    """
    this function takes a set of scores and returns depth scores for all local minima
    :param scores: list
    :return: list(tuple)
    """
    minima = set(argrelextrema(numpy.array(scores), numpy.less)[0])
    maxima = set(argrelextrema(numpy.array(scores), numpy.greater)[0])
    last_maxima = 0
    depth_scores = []  # a list of tuples (index_of_minima, depth_score_at_minima)
    for i in xrange(len(scores)):
        if i in maxima:
            last_maxima = i

        if i in minima:
            # find the next maxima
            next_maxima = None
            count = 0
            while next_maxima is None:
                count += 1
                if i + count in maxima:
                    next_maxima = i + count
                elif i + count == len(scores) - 1:
                    next_maxima = i + count
            depth_score = (scores[last_maxima] - scores[i]) + (scores[next_maxima] - scores[i])
            depth_scores.append((i, depth_score))

    return depth_scores


def boundarize(depth_scores, type='liberal'):
    """
    This function takes the depth scores and returns a list of indices where the boundaries should be. Has two
    modes: 'liberal' and 'conservative'.
    :param depth_scores: list(tuple)
    :param type: 'liberal'|'conservative'
    :return: list
    """
    average = numpy.mean([depth_score for i, depth_score in depth_scores])
    deviation = numpy.std([depth_score for i, depth_score in depth_scores])
    print average - (deviation/2.0)

    boundaries = []
    if type == 'liberal':
        for i, depth_score in depth_scores:
            if depth_score > average - deviation:
                boundaries.append(i)
    elif type == 'conservative':
        for i, depth_score in depth_scores:
            if depth_score > average - (deviation / 2.0):
                boundaries.append(i)

    return boundaries


def find_boundaries(scores, smoothing_window=2, type='liberal'):
    """
    This function does everything required to go from a list of similarity scores to a tuple of indexes where boundaries
    occur.
    :param scores: list
    :param smoothing_window: int  # must be even
    :param type: 'liberal'|'conservative'
    :return: tuple
    """
    smoothed_scores = smoothing(scores, smoothing_window)
    depth_scores = depth_scoring(smoothed_scores)
    boundaries = boundarize(depth_scores, type)
    return tuple(boundaries)
