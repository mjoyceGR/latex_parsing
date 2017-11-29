#!/usr/bin/env python
##############################################################################
#
# Author: M. Joyce 
#
# To run in terminal: 
#		>$ chmod +x introcites.py
# 		>$ ./introcites.py bibfile.bib latex.tex [out.tex]
#
# To run as filter:
# 		>$ :.! $DIR/introcites.py $DIR/bibfile.bib
# for e.g. current line in vim
#
##############################################################################
import sys
import subprocess
import re
import os

## Parses the bibtex article
## creates field names based on fields in bibtex entry
## assigns fields without bibtex names to "bib_ID"
def parse_bibtex_file(inputfile): 
	inside_entry = False
	after_comma = False
	after_equal = False
	brackets = 0 
	field=''
	entry=''
	articles = []

	with open(inputfile) as filef:
		c = filef.read(1) 
		while c != '':
			## pull data out of every text block starting with "@"		
			if c == "@": 	
				fields = {} 
				inside_entry= True

			if inside_entry:
				if c == '{':
					brackets = brackets +1
					if brackets ==1:
						after_comma =True

				elif c == '}':
					brackets = brackets -1
					if brackets ==0:
							articles.append(fields)
							## out of the @ block, reset everything
							inside_entry= False
							after_comma = False
							after_equal = False
							field = ''
							entry = ''

				elif c == "," and brackets == 1:
					## you're in the article, after one comma
					if field: 
						if entry: 
							fields[field.strip()] = entry.strip()
						else:
							fields['bib_ID'] = field

					after_comma = True
					after_equal = False
					field = ''
				elif c == "=" and brackets == 1:
					after_comma = False
					after_equal = True
					entry = ''
				else:
					if after_comma:
						field = field + c
					elif after_equal:
						entry = entry + c
			c = filef.read(1)
	return articles

## Reformats the author fields 
def format_authors(author_string):
	chardict={'~': '', '{' : '', '}':'', '-':'', '\n':'','\t':''} 
	author_string = multiple_replace(author_string,chardict)

	names=author_string.split(' and ') 
	lastnames=[]
	for  n in names:
		lastnames.append(n.split(',')[0])

	reformatted=''
	for i, s in enumerate(lastnames):
		s.strip()
		if len(lastnames) == 1:
			reformatted = reformatted+' '+s
		elif len(lastnames) <= 2:
			if i < len(lastnames)-1:
				reformatted=reformatted+' '+s
			else:
				reformatted=reformatted+' and '+s
		else:
			if i < len(lastnames)-1:
				reformatted=reformatted+' '+s+','
			else:
				reformatted=reformatted+' and '+s
	return reformatted	

## Constructs a dictionary of citation IDs:formatted author lists
def make_ID_author_dict(articles):
	cite_IDs=[]
	author_data=[]

	for a in articles:
		if a.get('author') and a.get('bib_ID'):
			author_data.append(a.get('author',None))
			cite_IDs.append(a.get('bib_ID',None))
		elif a.get('AUTHOR') and a.get('bib_ID'):
			author_data.append(a.get('AUTHOR', None))
			cite_IDs.append(a.get('bib_ID',None))

	formatted_authors=[]
	for j in range(len(author_data)):
		formatted_authors.append(format_authors(author_data[j]))

	#make (cite_IDs, formatted_authors) the keys and values in dictionary 
	objectdict=dict(zip(cite_IDs,formatted_authors))
	return objectdict

## Replaces all occurances of \cite* with the formatted CHECK 
def multiple_replace(text, objectdict):
	## More robust search for cite calls, allowing for spaces/newlines etc
	rx = re.compile(\
		'\\\cite[\n\s]*\[[\s\n]*[^\]]*[\s\n]*\][\n\s]*(?P<refs>\{[\s\n]*[^\}]*[\s\n]*\})'\
		'|\\\cite[\n\s]*\{[\s\n]*[^\}]*[\s\n]*\}'\
		)

	## Processes matches to regular expression
	def one_xlat(match):
		## deals with optional args before citation
		if'[' in match.group(0):
			optarg=match.group(0).split('[')[1].split(']')[0] 
			optarg=optarg.strip()
			cprint=' \cite[' + optarg + ']{'
		else:
			cprint = ' \cite{'

		## deals with case of braces in optional args,
		## e.g. \cite[theorem{xyz}]{Author}
		if match.group('refs'):
			temp = re.search(("(?<={)[^}]*(?=})"),match.group('refs')).group(0)
		else:
			temp = re.search(("(?<={)[^}]*(?=})"),match.group(0)).group(0)
		
		## deals with multiple keys in citation	
		citekeys = temp.split(',')
		citestring="\n %% CHECK CITATION\n"
		mainheader=citestring

		for i,citekey in enumerate(citekeys):
			citekey=citekey.strip()
			auth=objectdict.get(citekey)
			try:
				if len(citekeys) == 1:
					citestring = citestring+auth+cprint+citekey + "}"
				elif len(citekeys) <= 2:
					if i < len(citekeys)-1:
						citestring=citestring+auth+cprint+citekey + "}"
					else:
						citestring=citestring+" and"+auth+cprint+citekey + "}"
				else:
					if i < len(citekeys)-1:
						citestring=citestring+auth +cprint+citekey + "}," #check these
					else:
						citestring=citestring+" and"+auth +cprint+citekey + "}"	
			
			## If citation key is not in bibtex file,
			## insert warning as latex comment directly
			except TypeError: 
				citeheader='\n%% CHECK CITATION key'
				if len(citekeys) == 1:
					citestring = citestring+cprint+citekey + "}"
				elif len(citekeys) <= 2:
					if i < len(citekeys)-1:
						citestring=citestring+cprint+citekey + "}"
					else:
						citestring=citestring+" and"+cprint+citekey + "}"
				else:
					if i < len(citekeys)-1:
						citestring=citestring+cprint+citekey + "}," #check these
					else:
						citestring=citestring+" and"+cprint+citekey + "}"	

				citestring=citeheader + " '"+ citekey + "' not found in bibliography\n" + citestring 
				if mainheader in citestring:
					citestring=re.sub(mainheader,'',citestring)

		return citestring 
	sub = rx.sub(one_xlat,text)
	return sub

## Replace \cite{} calls in the latex file with new text
## based on dictionary of keys gleaned from the bibtex file
def find_replace(text,outfile,objectdict):
	## checks whether input arg is a file, if not, run as filter
	if os.path.isfile(text):
		f=open(text,"r")
		latex_file = f.read()
		f.seek(0)
		f.close()
		newcontents=multiple_replace(latex_file, objectdict)
		f = open(outfile, 'w')
		f.write(newcontents)
		f.close()
		return
	else:
		newcontents=multiple_replace(text, objectdict)
		f = open(outfile, 'a')
		f.write(newcontents)
		f.close()
		return newcontents

##-------------------------- main--------------------------
## Number of input arguments tells script whether it's running on a file or as a filter
if len(sys.argv) > 4:
	print "execute as \n./introcites.py bibname.bib texfile.tex [out.tex] \nto process files from command line"
	sys.exit(2)

elif 3 <= len(sys.argv) <= 4:
	bib_file=sys.argv[1]	
	tex_file=sys.argv[2]

	if len(sys.argv)==4:
		outfile = sys.argv[3]
	else:
		outfile=tex_file

	articles = parse_bibtex_file(bib_file) 
	objectdict = make_ID_author_dict(articles)
	find_replace(tex_file,outfile, objectdict) 

else:
	try:
		bib_file = sys.argv[1]
		input_text = sys.stdin.read() 
		articles = parse_bibtex_file(bib_file) 
		objectdict = make_ID_author_dict(articles)
		outfile="changes.temp"
		print find_replace(input_text,outfile,objectdict)

	except IndexError:
		print "Needs arguments" 
		