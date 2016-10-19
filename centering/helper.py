import tempfile,os,subprocess


def exec_via_temp(input_text, command_params, workdir=""):
	temp = tempfile.NamedTemporaryFile(delete=False)
	exec_out = ""
	try:
		temp.write(input_text)
		temp.close()

		command_params = [x if x != 'tempfilename' else temp.name for x in command_params]
		if workdir == "":
			proc = subprocess.Popen(command_params, stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
			(stdout, stderr) = proc.communicate()
		else:
			proc = subprocess.Popen(command_params, stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE,cwd=workdir)
			(stdout, stderr) = proc.communicate()

		exec_out = stdout
	except Exception as e:
		print e
	finally:
		os.remove(temp.name)
		return exec_out

def make_cf_input(xrenner_obj):
	output = ""
	for markable in xrenner_obj.markables:
		output += "\t".join([str(markable.sentence.sent_num),markable.head.text,markable.func,markable.entity]) + "\n"
	return output.replace("\r","")

def make_cf_list(cf_table):
	out_sents = []
	temp_list =[]
	last_col = "1"
	for line in cf_table.split("\n"):
		cols = line.split("\t")
		if last_col == cols[0]: # Still the same sentence
			temp_list.append(cols[1])
		else:
			out_sents.append(temp_list)
			temp_list = []
		last_col = cols[0]
	return out_sents

