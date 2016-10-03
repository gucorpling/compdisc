#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-

print "Content-Type: text/html\n\n\n"


from tile_vintro import tile as vintro
from word_vecs import tile as vecs
from lexical_chains import LexicalChains
from tile_reader import TileReader
import cgi,re,platform

input_text = "Paste some text here (about 20-100 sentences)."

form = cgi.FieldStorage()
analysis = ""
tiled = ""
output_mode = "binary"
sentences = []
method = "vintro"


vec_options = {'vocab_tags': ["NOUN", "PROPN"],
           'block_length': 3,
           'smoothing_window': 2,
           'smoothing_type': 'liberal',  # liberal or conservative
           'out_type': 0}  # 0 or 1



if "input_text" in form:
	input_text = form.getvalue("input_text")
	if len(input_text) > 8000:
		input_text = "Input too long for Web demo."
	input_text = re.sub(r'''[^%#A-Za-z0-9\.'"!\?, _\t\n\$/;`:<>=@&\[\]\)\r\(\+-]''',"",input_text) # Wipe non-ascii chars. TODO: better Unicode handling
	method = form.getvalue("method")
	output_mode = form.getvalue("output")
	input_text = input_text.replace("\r","")
	if method == "vecs":
		analysis, reader = vecs(input_text, vec_options, True)
	elif method == "chains":
		# Instantiate TileReader
		reader = TileReader()
		reader.read(input_text, True)
		sents = reader.sentences

		# Instantiate Lexical Chains
		chains = LexicalChains()
		chains.analyze(sents)
		analysis = chains.boundary_vector
	else:
		analysis, reader = vintro(input_text,True)

	sentences = reader.sentences

	for index, sent in enumerate(sentences):
		if analysis[index] == 1 and index > 0:
			tiled += "<br/>----------<br/>\n"
		tiled += str(sent) + "\n"
	if output_mode == "binary":
		analysis = ",".join([str(bit) for bit in analysis])
	else:
		analysis = tiled


if platform.system() == "Windows":
	template = open("compdisc/webtile.html").read()
else:
	template = open("webtile.html").read()

output = template.replace("**input_text**",input_text)
output = output.replace("**analysis**",analysis)
output = output.replace('value="'+ output_mode + '"', 'value="'+ output_mode + '" selected')
output = output.replace('value="'+ method + '"', 'value="'+ method + '" selected')

print output
