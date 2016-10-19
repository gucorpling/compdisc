"""
coherence evaluator
"""

import argparse
import os
import sys
from depedit.depedit import DepEdit
from xrenner.modules.xrenner_xrenner import Xrenner

# Centering module imports
from cb_finder import cb_finder
from compdisc.vectors import Vectors
from bridging import bridging
# ToDo: Need cf module


# ======================================================================================================================
# Main
# ======================================================================================================================
def main(text):

    # FORMAT
    parsed = parse(text)

    # BRIDGING
    # ToDo: James, is there a reason the vector stuff isn't all just under the centering directory?
    vectors = Vectors(optimize=False, filename="{}{}vectors{}GoogleNewsVecs.txt".format(
        os.path.join(os.getcwd(), os.pardir), os.sep, os.sep))
    bridging(parsed, vectors)

    # CFS
    cfs = centered_f(parsed)

    # CBS
    cbs = cb_finder(parsed)

    # CLASSIFY
    transitions = classify_transitions(cfs, cbs)

    # SCORE
    score = scoring(transitions)
    print "COHERENCE: {}".format(score)

    return


# ======================================================================================================================
# Funcs
# ======================================================================================================================
def parse(text_file):
    with open(text_file, "rb") as f:
        text = unicode(f.read())

    if text_file.endswith(".conll10"):
        edited = text

    elif text_file.endswith(".txt"):
        # Get parse from Spacy
        from spacy.en import English
        parser = English(entity=False, load_vectors=False, vectors_package=False)
        parsed = parser(text)

        # Transform to conll format
        parsed_string = ""
        prev_s_toks = 0
        for sent in parsed.sents:
            toks = 0
            for index, token in enumerate(sent):
                toks += 1
                # skip if token is newline.
                if token.orth_ == "\n":
                    continue
                if token.head.i + 1 - prev_s_toks == token.i + 1 - prev_s_toks:
                    head_id = 0
                else:
                    head_id = token.head.i + 1 - prev_s_toks

                line = [str(token.i + 1 - prev_s_toks), token.orth_, token.lemma_, token.tag_, token.pos_, "_",
                        str(head_id), token.dep_, "_", "_"]
                parsed_string += "\t".join(line) + "\n"
            prev_s_toks += toks
            parsed_string += "\n"

        # setup config
        config = "func=/ROOT/\tnone\t#1:func=root\n"
        config += "func=/relcl/\tnone\t#1:func=rcmod\n"
        config += "func=/nummod/\tnone\t#1:func=num\n"
        config += "lemma=/be/&func=/(.*)/;func=/nsubj/;func=/attr/;text=/.*/\t#1>#2;#1>#3;#4>#1\t#4>#3;#3>#1;#3>#2;#1:func=cop;#3:func=$1\n"
        config += "lemma=/be/&func=/root/;func=/nsubj/;func=/attr/\t#1>#2;#1>#3\t#3>#1;#3>#2;#1:func=cop;#3:func=root\n"

        # Setup depedit
        deped = DepEdit(config.split("\n"))

        # Run depedit
        edited = deped.run_depedit(parsed_string.split("\n"))

    else:
        sys.exit("Unknown input file type")

    # Get and return Xrenner object
    xobj = Xrenner(override="GUM")
    xobj.analyze(edited, "conll")
    return xobj


def centered_f(bridged):
    # ToDO: Replace dummy function with Akitaka's cf module
    fake_cfs = [["I", "experience"], ["i", "small-businessman"], ["he"], ["he", "fabrics", "tables", "paint"]]
    return fake_cfs


def get_antecedent(markable):
    """
    Recursively finds deepest antecedent of a given xrenner markable
    :param markable: xrenner markable
    :return: text representation of deepest antecedent
    """
    # if markable.antecedent is not 'none':
    #    return get_antecedent(markable.antecedent)
    # else:
    #    return markable.text.lower()
    while True:
        if markable.antecedent is 'none':
            return markable.text.lower()
        else:
            markable = markable.antecedent


def classify_transitions(cfs, cbs):
    """
    Classifies type (continue, retain, smooth shift, rough shift) and cost (cheap, expensive) of each sentence
    transition in document
    :param cfs: list containing ranked lists of markables
    :param cbs: list containing lists of markables
    :return: list of (type, cost) tuples
    """
    # ToDo: Add in logic to find best path in the case of cb ties
    assert (len(cfs) == len(cbs))

    transitions = []
    for i in xrange(1, len(cbs)):

        # Assign cp/cb variables
        cp_n = cfs[i][0].lower()
        cp_prev = cfs[i - 1][0].lower()
        cb_n = cbs[i][0] if not cbs[i][0] else get_antecedent(cbs[i][0])
        cb_prev = cbs[i - 1][0] if not cbs[i - 1][0] else get_antecedent(cbs[i - 1][0])

        # Classify transition type
        if not cb_prev or (cb_n == cb_prev):
            if cb_n == cp_n:
                type = "continue"
            else:
                type = "retain"
        else:
            if cb_n == cp_n:
                type = "smooth_shift"
            else:
                type = "rough_shift"

        # Classify transition cost (according to Strube & Hahn 1999)
        if cb_n == cp_prev:
            cost = "cheap"
        else:
            cost = "expensive"

        transitions.append((type, cost))

    return transitions


def scoring(transitions):
    """
    Calculates composite coherence score of document based on transition types and costs
    :param transitions: list of (type, cost) tuples
    :return: float
    """
    type_vals = {
        "continue": 3,
        "retain": 2,
        "smooth_shift": 1,
        "rough_shift": 0,
    }

    cost_vals = {
        'expensive': 0,
        'cheap': 1
    }

    # Get scores for each transition in doc
    type_score = sum([type_vals[trans[0]] for trans in transitions])
    cost_score = sum([cost_vals[trans[1]] for trans in transitions])

    # Normalize scores for each transition in doc
    type_score_adjusted = float(type_score) / (type_vals["continue"] * len(transitions))
    cost_score_adjusted = float(cost_score) / (cost_vals["cheap"] * len(transitions))

    # Assign weights to transition types and costs
    type_weight = 2
    cost_weight = 1

    # Combine weighted scores for transition type and cost to get total adjusted coherence score
    total_adjusted = (type_weight*type_score_adjusted + cost_weight*cost_score_adjusted) / (type_weight + cost_weight)

    return total_adjusted


# ======================================================================================================================
# Run
# ======================================================================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help="text file containing input to parse", action="store", dest="input",
                        required=True)

    args = parser.parse_args()

    main(args.input)
