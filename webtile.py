#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-

print "Content-Type: text/html\n\n\n"


from tile_vintro import tile as vintro
from word_vecs import tile as vecs
from lexical_chains import LexicalChains
from tile_reader import TileReader
import cgi,re,platform

input_text = """Coron is in the province of Palawan , Philippines on Busuanga Island .
It is the largest town on the island and has the largest share of accommodations .
Coron is both the name of the largest town on the island of Busuanga , and the name of a different , smaller island just offshore .
The area is famous for its World War II wreck diving , and the site has been named in many lists of top dive spots in the world .
In September 1944 , a fleet of Japanese ships hiding in the harbor were sunk in a daring raid by the US navy .
The result is around ten well preserved underwater shipwrecks surrounded with coral reef .
There are also attractions on Coron Island itself .
There are many beautiful white sand beaches , mostly tiny and surrounded by large limestone cliffs and wildlife .
Barracuda and Kayangan lakes are both stunning locations , and good for snorkeling , and the island is the ancestral domain of an indigenous tribe who are managing the island in a sustainable way and keeping outsiders at a distance and offshore at night .
The first inhabitants of Coron were the Tagbanuas who belong to the second wave of Indonesians who migrated to this area some 5,000 years ago .
They were a nomadic , seafaring people , living mainly by fishing and subsistence agriculture .
Although they are now sedentary ( with the young using cell phones , etc. ) , they maintain many of their old customs , traditions and beliefs .
Today , the Tagbanuas remain the dominant if not entire population of Coron .
In 1902 that Coron was registered as a town and the name of the town was officially changed from Penon de Coron to Coron .
From 1939 to the outbreak of World War II , the municipality experienced the mining boom .
Labor shifted from farming to mining .
In July 1942 the Japanese occupied the mining camps and resumed operation of the manganese mines .
On September 24 , 1944 , a group of Japanese ships were sunk by American warplanes in Coron waters as the ships retreated from Manila Bay .
To this day , about 10 or 12 of these World War II Japanese shipwrecks comprise what is considered one of the best dive sites in the world .
In 1947 , large scale deep sea fishing was introduced to Coron , and the town experienced another boom , a fishing boom .
The population increased , as many people from Luzon and the Visayas came to work either as fishermen or miners .
On June 17 , 1950 , Busuanga was officially created as a separate municipality from Coron and in 1954 , Coron was further reduced by the official creation of the Municipality of Linapacan .
On September 12 , 1992 , Coron was finally reduced by the official creation of the Municipality of Culion .
In the past , Coron was virtually unknown outside of Palawan .
It remains a small , quaint fishing town with laid back charm but with increasing media exposure it is growing , slowly but steadily .
Coron has taken an important position in the tourism industry .
In the past decade , there has been a rapid influx of scuba divers and other tourists coming in , making tourism the major industry player in Coron today .
"""

form = cgi.FieldStorage()
analysis = ""
tiled = ""
output_mode = "text"
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
