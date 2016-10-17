"""
coherence evaluator
"""

import argparse
import os
import sys
from spacy.en import English
from depedit.depedit import DepEdit
from xrenner.modules.xrenner_xrenner import Xrenner

# Module imports
from cb_finder import cb_finder


# ======================================================================================================================
# Main
# ======================================================================================================================
def main(text):
    parsed = parse(text)
    bridged = bridging(parsed)
    cfs = centered_f(bridged)
    cbs = cb_finder(bridged)
    transitions = classify_transitions(cfs, cbs)
    score = scoring(transitions)
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
                if token.head.i + 1 - prev_s_toks == token.i + 1 - prev_s_toks:  # Spacy represents root as self-dominance, revert to 0
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
    xobj = Xrenner(model=os.path.join(os.getcwd(), "eng.xrm"), override="GUM")
    xobj.analyze(edited, "conll")

    return xobj


def centered_f(bridged):
    #return list of ranked cfs for each sent in doc. structure should be a list of lists.
    return bridged


def bridging(parsed):
    #return enriched xrenner obj
    return parsed

def classify_transitions(cfs, cbs):
    assert(len(cfs) == len(cbs))

    transitions = []
    for i, cb in enumerate(cbs):
        cp = cfs[i][0]
        if i == 0:
            continue

        if (cbs[i-1] is None) or (cbs[i] == cbs[i-1]):
            if cbs[i] == cp:
                type = "continue"
            else:
                type = "retain"
        else:
            if cbs[i] == cp:
                type = "smooth_shift"
            else:
                type = "rough_shift"

        transitions.append(type)

    return transitions

def scoring(transitions):
    return


# ======================================================================================================================
# Run
# ======================================================================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help="text file containing input to parse", action="store", dest="input",
                        required=True)

    args = parser.parse_args()

    main(args.input)