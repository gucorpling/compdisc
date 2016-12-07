"""
tagger.py

input: two conll10 files -- one training file, one test file w/gold relation labels
output: conll10 test file with predicted relations in 4th column (named "relation_tagger_output.txt" by default)

usage: python tagger.py -t <training file> -g <test file w/gold relation labels> [-e <# of evaluation iterations>]
Note: Use optional param -e <number> to evaluate & print avg accuracy over the specified number of testing iterations

example: python tagger.py -t gum_rsd_malt_train.conll -g gum_rsd_malt_gold.conll -e 5
"""

import re
import argparse
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.grid_search import GridSearchCV
from collections import Counter


# ======================================================================================================================
# Main
# ======================================================================================================================
def tag(train, gold, evaluate=0):
    # parse each edu in training and test files
    parsed_train = parse_rst(train)
    parsed_gold = parse_rst(gold)

    # extract feature array for both training and test files
    train_feats = extract_features(parsed_train, data_type="train")
    gold_feats = extract_features(parsed_gold, data_type="gold")

    # combine into one array for factorization
    both = train_feats + gold_feats

    # factorize features in feature array in order to create numpy arrays
    # (and save mapping of rst relations to numeric factors)
    feat_matrix, label_dict = factorize(both)

    # extract training and test sets from feature matrix
    training_features, training_labels, test_features, gold_labels = extract_dataset(feat_matrix)

    # train classifier, get predictions
    predictions, n_estimators, max_features = classify(training_features, training_labels, test_features, gold_labels)

    # Evaluate classifier if desired
    if evaluate:
        score(training_features, training_labels, test_features, gold_labels, n_estimators, max_features,
              niters=evaluate)

    # splice predicted labels into testing data
    output_lines = format_output(parsed_gold, predictions, label_dict)

    # write output to file
    write_out(output_lines)


# ======================================================================================================================
# Parsing
# ======================================================================================================================
def parse_rst(input):
    with open(input, "rb") as f:
        raw = f.read()
    lines = raw.split("\n")
    parsed = [ParsedLine(line) for line in lines if line]
    return parsed


class ParsedLine(object):
    # todo: this class has gotten real hacky after screwing around with the lexical features. Instead of doing all the
    # todo: (cont.) feature stuff here, just pull it all out in extract_features() and make this a simple class.

    def __init__(self, raw):
        self.raw = raw
        self.depth = 0
        self.head = ""
        self.head_sfx = ""
        self.second = ""
        self.type = ""
        self.head_pos = ""
        self.relation = ""
        self.relation_short = ""
        self.length = 0
        self.func = ""
        self.subord = 0
        self.date = 0
        self.caption = 0
        self.para = 0
        self.heading = 0
        self.item = 0
        self.list = 0
        self.toks = []
        self.length = 0
        self.PRP_num = 0
        self.WP_num = 0
        self.NP_num = 0
        self.NN_num = 0
        self.has_PRP = 0
        self.has_NP = 0
        self.has_WP = 0

        # Parse preamble
        pattern = r"([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t[^\t]*\t([^\t]*)[^\t]*\t[^\t]*\t|||"
        self.depth, self.head, self.second, self.type, self.head_pos, feat, self.relation = re.search(pattern, self.raw).groups()
        self.relation_short = re.sub(r'_(m|r)', r'', self.relation)

        feats = feat.split("|")
        self.length = int(feats[0])
        self.func = feats[1]
        if "LEFT" in feats:
            self.subord = 1
        if "RIGHT" in feats:
            self.subord = 2
        if "date" in feats:
            self.date = 1
        if "caption" in feats:
            self.caption = 1
        if "open_para" in feats:
            self.para = 1
        if "head" in feats:
            self.heading = 1
        if "open_item" in feats:
            self.item = 1
        if ("ordered" or "unordered") in feats:
            self.list = 1

        # Parse tokens
        text = re.sub(pattern, r"", self.raw, count=1)
        raw_toks = text.split("///")
        self.toks = [ParsedToken(raw_tok) for raw_tok in raw_toks if raw_tok]

        # additional features
        self.PRP_num = len([tok for tok in self.toks if "PRP" in tok.pos])
        self.WP_num = len([tok for tok in self.toks if "WP" in tok.pos])
        self.NP_num = len([tok for tok in self.toks if "NP" in tok.pos])
        self.NN_num = len([tok for tok in self.toks if "NN" in tok.pos])

        self.has_PRP = 1 if self.PRP_num != 0 else 0
        self.has_NP = 1 if self.NP_num != 0 else 0
        self.has_WP = 1 if self.WP_num != 0 else 0

        self.head_sfx = self.head[-2:]

        # Lexical features (based on freq analysis)
        lemmas = [tok.lemma for tok in self.toks]
        self.has_card = 1 if "@card@" in lemmas else 0
        self.cop = 1 if "be" in lemmas else 0
        self.iff = 1 if "if" in lemmas else 0
        self.when = 1 if "when" in lemmas else 0
        self.you = 1 if "you" in lemmas else 0
        self.me = 1 if "I" in lemmas or "me" in lemmas else 0
        self.do = 1 if "do" in lemmas else 0
        self.because = 1 if "because" in lemmas else 0
        self.that = 1 if "that" in lemmas else 0
        self.orr = 1 if "or" in lemmas else 0
        self.what = 1 if "what" in lemmas else 0
        self.method = 1 if "because" in lemmas else 0
        self.nott = 1 if "not" in lemmas else 0
        self.forr = 1 if "for" in lemmas else 0
        self.instead = 1 if "instead" in lemmas else 0
        self.although = 1 if "although" in lemmas else 0
        self.however = 1 if "however" in lemmas else 0
        self.ass = 1 if "as" in lemmas else 0
        self.have = 1 if "have" in lemmas else 0
        self.this = 1 if "this" in lemmas else 0
        self.that = 1 if "that" in lemmas else 0
        self.but = 1 if "but" in lemmas else 0
        self.nt = 1 if "n't" in lemmas else 0
        self.a = 1 if "a" in lemmas else 0
        self.the = 1 if "the" in lemmas else 0
        self.will = 1 if "will" in lemmas else 0
        self.was = 1 if "was" in lemmas else 0
        self.interview = 1 if "interview" in lemmas else 0
        self.result = 1 if "result" in lemmas else 0
        self.on = 1 if "on" in lemmas else 0
        self.q = 1 if "?" in lemmas else 0
        self.brack = 1 if "(" in lemmas else 0
        self.quote = 1 if '"' in lemmas or "'" in lemmas else 0
        self.asfor = 1 if "as" in lemmas and "for" in lemmas else 0



class ParsedToken(object):
    def __init__(self, tok):
        fields = tok.split("|||")
        self.raw = fields[1]
        self.lemma = fields[2]
        self.pos = fields[4]
        self.func = fields[7]


# ======================================================================================================================
# Feature extraction & Factorization
# ======================================================================================================================
def factorize(feat_matrix):
    # Make sure length of set(lengths) is 1 (i.e. all feature lists are same size)
    list_lengths = [len(lst) for lst in feat_matrix]
    assert(len(set(list_lengths)) == 1)

    # Factorize each feature
    label_dict = {}
    for i in range(list_lengths[0]):
        if i == 0:  # skip edu ID
            continue
        else:
            # Get list of unique types for feature i, create factor dictionary
            types = set([lst[i] for lst in feat_matrix])
            type_dict = {type: float(k) for k, type in enumerate(types)}

            # save factor_dict for relation labels so we can reconstitute these later
            if i == 1:
                label_dict = {v: k for k, v in type_dict.iteritems()}

            # factorize feature
            for lst in feat_matrix:
                lst[i] = type_dict[lst[i]]

    # Check to make sure everything is still kosher
    list_lengths = [len(lst) for lst in feat_matrix]
    assert (len(set(list_lengths)) == 1)
    assert all(isinstance(key, float) for key in label_dict.keys())
    assert all(isinstance(val, str) for val in label_dict.values())
    return feat_matrix, label_dict


def extract_features(parsed_lines, data_type="undef"):
    # todo: there's a cleaner way to do this... don't have time now.
    group_feats = []
    for i, line in enumerate(parsed_lines):
        features = [
            "{}{}".format(data_type, i),
            line.relation_short,
            line.type,
            line.depth,
            line.head_pos,
            line.head_sfx,
            line.length,
            line.func,
            line.subord,
            line.date,
            line.caption,
            line.para,
            line.heading,
            line.item,
            line.list,
            line.PRP_num,
            line.WP_num,
            line.NP_num,
            line.NN_num,
            line.has_PRP,
            line.has_NP,
            line.has_WP,
            line.has_card,
            line.cop,
            line.iff,
            line.when,
            line.you,
            line.me,
            line.do,
            line.because,
            line.that,
            line.orr,
            line.what,
            line.method,
            line.nott,
            line.forr,
            line.instead,
            line.although,
            line.however,
            line.ass,
            line.have,
            line.this,
            line.that,
            line.but,
            line.nt,
            line.a,
            line.the,
            line.will,
            line.was,
            line.interview,
            line.result,
            line.on,
            line.q,
            line.brack,
            line.quote,
            line.asfor,
        ]

        if i == 0:
            prev_feats = [
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
            ]
        else:
            prev_feats = [
                parsed_lines[i-1].type,
                parsed_lines[i-1].depth,
                parsed_lines[i-1].head_pos,
                parsed_lines[i-1].head_sfx,
                parsed_lines[i-1].length,
                parsed_lines[i-1].func,
                parsed_lines[i-1].subord,
                parsed_lines[i-1].date,
                parsed_lines[i-1].caption,
                parsed_lines[i-1].para,
                parsed_lines[i-1].heading,
                parsed_lines[i-1].item,
                parsed_lines[i-1].list,
                parsed_lines[i-1].PRP_num,
                parsed_lines[i-1].WP_num,
                parsed_lines[i-1].NP_num,
                parsed_lines[i-1].NN_num,
                parsed_lines[i-1].has_PRP,
                parsed_lines[i-1].has_NP,
                parsed_lines[i-1].has_WP,
                parsed_lines[i-1].has_card,
                parsed_lines[i-1].cop,
                parsed_lines[i-1].iff,
                parsed_lines[i-1].when,
                parsed_lines[i-1].you,
                parsed_lines[i-1].me,
                parsed_lines[i-1].do,
                parsed_lines[i-1].because,
                parsed_lines[i-1].that,
                parsed_lines[i-1].orr,
                parsed_lines[i-1].what,
                parsed_lines[i-1].method,
                parsed_lines[i-1].nott,
                parsed_lines[i-1].forr,
                parsed_lines[i-1].instead,
                parsed_lines[i-1].although,
                parsed_lines[i-1].however,
                parsed_lines[i-1].ass,
                parsed_lines[i-1].have,
                parsed_lines[i-1].this,
                parsed_lines[i-1].that,
                parsed_lines[i-1].but,
                parsed_lines[i-1].nt,
                parsed_lines[i-1].a,
                parsed_lines[i-1].the,
                parsed_lines[i-1].will,
                parsed_lines[i-1].was,
                parsed_lines[i-1].interview,
                parsed_lines[i-1].result,
                parsed_lines[i-1].on,
                parsed_lines[i-1].q,
                parsed_lines[i-1].brack,
                parsed_lines[i-1].quote,
                parsed_lines[i-1].asfor,
            ]
        features = features + prev_feats
        group_feats.append(features)
    return group_feats


# ======================================================================================================================
# train/test split and classification/prediction
# ======================================================================================================================
def extract_dataset(feat_matrix):
    """
    Separate relations from features, remove relations and id from feature lists
    :param feat_matrix:
    :return:
    """
    training_labels = []
    training_features = []
    gold_labels = []
    test_features = []

    for lst in feat_matrix:
        if "train" in lst[0]:
            training_labels.append(float(lst[1]))
            training_features.append([float(feat) for feat in lst[2:]])
        elif "gold" in lst[0]:
            gold_labels.append(float(lst[1]))
            test_features.append([float(feat) for feat in lst[2:]])

    # Make lists into numpy arrays
    training_labels = np.array(training_labels)
    gold_labels = np.array(gold_labels)
    training_features = np.array(training_features)
    test_features = np.array(test_features)

    # Make sure you haven't gotten any wires crossed
    assert len(training_labels) == len(training_features)
    assert len(gold_labels) == len(test_features)
    return training_features, training_labels, test_features, gold_labels


def classify(training_features, training_labels, test_features, gold_labels, optimize=False, niters=1, verbose=False,
             evaluate=False):

    if optimize:
        # create parameter grid
        clf = RandomForestClassifier(n_estimators=20, n_jobs=-1)
        param_grid = {
            'n_estimators': (100, 300, 500, 700),
            'max_features': range(1, 20)
        }

        # Optimize
        print "optimizing..."
        CV_clf = GridSearchCV(estimator=clf, param_grid=param_grid, cv=5, n_jobs=-1)
        CV_clf.fit(training_features, training_labels)

        # Select best parameters
        max_features = CV_clf.best_params_['max_features']
        n_estimators = CV_clf.best_params_['n_estimators']
        print "best params: \n\tn_estimators: {}\n\tmax_features: {}".format(n_estimators, max_features)
    else:
        max_features = 25
        n_estimators = 500

    rfc = RandomForestClassifier(n_estimators=n_estimators, max_features=max_features, n_jobs=-1)
    rfc.fit(training_features, training_labels)
    predictions = rfc.predict(test_features)
    return predictions, n_estimators, max_features


# ======================================================================================================================
# Classifier evaluation
# ======================================================================================================================
def score(training_features, training_labels, test_features, gold_labels, n_estimators, max_features, niters=1,
          verbose=False):
    scores = []
    for iter in range(niters):
        print "\nIter {}: fitting model with {} n_estimators and {} max_features".format(iter + 1, n_estimators,
                                                                                         max_features)
        rfc = RandomForestClassifier(n_estimators=n_estimators, max_features=max_features, n_jobs=-1)
        rfc.fit(training_features, training_labels)

        print "predicting..."
        predictions = rfc.predict(test_features)

        zipped = zip(gold_labels, predictions)

        if verbose:
            for gold, pred in zipped:
                print "true: {}\tpredicted: {}".format(gold, pred)

        score = get_score(zipped)
        baseline = get_baseline(gold_labels)

        print "\nPercent correct: {}".format(score)
        print "Baseline: {}".format(baseline)

        scores.append(score)

    print "\n\nAVG Accuracy over {} iterations: {}".format(niters, (sum(scores) / len(scores)))


def get_score(zipped):
    ncorrect = 0
    ntotal = 0
    for x, y in zipped:
        ntotal += 1
        if x == y:
            ncorrect += 1

    score = float(ncorrect) / float(ntotal)
    return score


def get_baseline(gold_labs):
    labfreqs = Counter(gold_labs)
    most_freq = labfreqs.most_common(1)[0][0]
    count = labfreqs[most_freq]
    baseline = float(count) / float(len(gold_labs))
    return baseline


# ======================================================================================================================
# output
# ======================================================================================================================
def format_output(parsed_gold, predictions, label_dict):
    predictions_text = [label_dict[pred] for pred in predictions]
    out_lines = []
    for i, line in enumerate(parsed_gold):
        elements = line.raw.split("\t")
        elements[7] = "_"  # replace gold relation labels with underscores
        elements.insert(3, predictions_text[i])  # insert predicted labels
        out_lines.append("\t".join(elements))
    return out_lines


def write_out(output_lines):
    with open("relation_tagger_output.txt", "wb") as f:
        for line in output_lines:
            f.write(line + "\n")


# ======================================================================================================================
# run
# ======================================================================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--training", help="training file", action="store", dest="training_file")
    parser.add_argument("-g", "--gold", help="test file with gold rst relations", action="store", dest="gold_file")
    parser.add_argument("-e", "--evaluate", help="number of evaluation iterations", action="store", dest="eval",
                        default=False, required=False)

    opts = parser.parse_args()
    eval = int(opts.eval)

    tag(opts.training_file, opts.gold_file, evaluate=eval)
