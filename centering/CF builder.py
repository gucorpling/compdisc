def cf_builder(outputToR="outputToR.tsv", trainingData = 'dermovate.ne3.massimo.tagged', path2script = 'cf training.r'):
    """
    1. This function takes a well-organized text file with the following tsv format and returns the ranking of each element.
    2. The ranking is estimated by the logistic regression to predict how likely it is that the element becomes the next CB.
    3. The training data used in this process should be matched with the GNOME corpus format.
    4. Be sure that you put the required R (= path2script) in the appropriate directory.

    :param outputToR: This is a file that has the following format with the order of "text", "sentence ID", "grammatical form"
    , "ontological entity", "gender agreement feature", "informatino status".
        >HOW YOU GET THE MARKABLES
        All of them are extractable from xrenner.markables.
    	file.write(each_markable.text)
    	file.write(each_markable.form)
    	file.write(each_markable.entity)
    	file.write(each_markable.agree)
	    file.write(each_markable.infstat)
	    file.write(re.sub('^[^\\-]*?\\-([^\\-]*?)\\-.*$','\\1',str(each_markable.head)))

        >THE Expected INPUT FORMAT
        The CEO,1,common,person,male,new,nsubj
        The CEO and the taxi driver,1,common,person,plural,new,nsubj
        the taxi driver,1,common,person,,new,nsubj
        His,1,pronoun,person,male,giv,poss
        His employees,1,common,person,plural,new,nsubj
        them,1,pronoun,person,plural,giv,dobj

    :param trainingData: The model is trained against the GNOME data. Such as "dermovate.ne3.massimo.tagged",
     and "estracombi.ne3.massimo.tagged" If you would like to use both of them, or more, please make the combined file
     before putting it in the input argument.
    :param path2script: The path to the R script, which is by default named "cf builder.r"
    :return: the standard output consists of a line for each item with the text name on your left collumn and with the ranking on your right collumn.
    The two collumns are combined with "\t" (tab).
    """
    import subprocess
    # Define command and arguments
    command = 'Rscript'
    # Variable number of args in a list
    args = [outputToR,  trainingData]
    # (1) the first argument is the file you created above
    # (2) from the second argument to the las, you specify the training data from gnome corpus with the extension of .tagged

    # Build subprocess command
    cmd = [command, path2script] + args
    # check_output will run the command and store to result
    x = subprocess.check_output(cmd, universal_newlines=True)
    print(x)