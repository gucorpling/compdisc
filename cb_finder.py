from xrenner.modules.xrenner_xrenner import Xrenner
from spacy.en import English
from depedit.depedit import DepEdit
import re


def cb_finder(xrenner):
    '''
    :param xrenner: an analyzed xrenner object
    :return: a list of lists where each inner list corresponds to a sentence,
    and contains either:
    -one of more markable object representing likely cbs,
    -None if the sentence contains no markables
    -False if there are markables but none a coreferent to previous sentence
    '''
    all_markables = xrenner.markables

    sent_count = xrenner.sent_num - 1
    marks_by_sent = [[] for sent in xrange(sent_count)]
    cb_by_sent = [[] for sent in xrange(sent_count)]

    for markable in all_markables:
        marks_by_sent[markable.sentence.sent_num - 1].append(markable)

    for s in xrange(sent_count):
        if len(marks_by_sent[s]) >= 1:
            # get list of markables with antecedents in prev sentence
            candidates = []
            for mark in marks_by_sent[s]:
                if mark.antecedent != "none":
                    if mark.antecedent.sentence.sent_num == mark.sentence.sent_num - 1:
                        candidates.append(mark)

            if len(candidates) >= 1:  # multiple candidates, need to choose
                
                # Rule 1
                pron_candidates = filter(lambda m: m.form == "pronoun", candidates)
                if len(pron_candidates) >= 1:
                    cb_by_sent[s] = pron_candidates
                else:
                    cb_by_sent[s] = candidates
            else:
                cb_by_sent[s] = [False]
        else:
            cb_by_sent[s] = [None]

    return cb_by_sent


if __name__ == "__main__":
    # Part 1: Use spacy to get a dependency parse of the text

    text = u"""I have a different experience.
     My father was a small-businessman.
     He worked really hard.
     He printed drapery fabrics on long tables, where he pulled out those fabrics and he went down with a silkscreen and
     dumped the paint in and took the squeegee and kept going."""
    # text = u"""John likes Mary.
    # John really likes her.""" # rule 1 test
    parser = English(entity=False,load_vectors=False,vectors_package=False)
    parsed = parser(text)


    # Part 2: xrenner expects Stanford typed dependencies
    # We can get these by running the Stanford Parser with 'basic' dependencies in 'conllx' format
    # Or we can use spacy, slightly rewire the results and labels, and construct conll format, as follows:
    parsed_string=""
    toks = 0
    prev_s_toks = 0
    for sent in parsed.sents:
        toks = 0
        for index, token in enumerate(sent):
            if token.head.i+1 - prev_s_toks == token.i+1 - prev_s_toks: # Spacy represents root as self-dominance, revert to 0
                head_id = 0
            else:
                head_id = token.head.i + 1 - prev_s_toks

            line = [str(token.i+1 - prev_s_toks),re.sub(r'\n', r'', token.orth_),re.sub(r'\n', r'', token.orth_),token.tag_,token.pos_,"_", str(head_id), token.dep_, "_","_"]
            parsed_string += "\t".join(line) + "\n"
            toks += 1
        prev_s_toks += toks
        parsed_string += "\n"

    #print parsed_string

    # Part 3: editing the labels to be Stanford-like
    # This part uses depedit: a module to do 'find and replace' in dependency trees
    # To learn more about how it works, see the user guide at: http://corpling.uis.georgetown.edu/depedit

    config =  "func=/ROOT/\tnone\t#1:func=root\n"
    config += "func=/relcl/\tnone\t#1:func=rcmod\n"
    config += "func=/nummod/\tnone\t#1:func=num\n"
    config += "lemma=/be/&func=/(.*)/;func=/nsubj/;func=/attr/;text=/.*/\t#1>#2;#1>#3;#4>#1\t#4>#3;#3>#1;#3>#2;#1:func=cop;#3:func=$1\n"
    config += "lemma=/be/&func=/root/;func=/nsubj/;func=/attr/\t#1>#2;#1>#3\t#3>#1;#3>#2;#1:func=cop;#3:func=root\n"

    deped = DepEdit(config.split("\n"))

    edited = deped.run_depedit(parsed_string.split("\n"))


    # Part 4: actual coref stuff

    # Load a model to initialize the Xrenner object with language specific lexical information
    xrenner = Xrenner(override="GUM")  # If you omit the gum override, you will get the OntoNotes schema, which ignores singleton mentions among other things
    analyzed = xrenner.analyze(edited, "conll")
    print cb_finder(xrenner)