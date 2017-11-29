#!/usr/bin/env python3
##############################################
#
# module name: doi
# use by placing in working repository and including
#
# 	 import doi
#
# in desired python3 code
#
# Author: M. Joyce 
#
#############################################
import subprocess
import datetime
import re

def grab_page(doi_url):
# grab html and store it as text file named doi_[current time]
	timetag=datetime.datetime.now()
	timetag = str(timetag.hour) + str(timetag.minute) + str(timetag.second) + str(timetag.microsecond)
	source_doi=doi_url
	subprocess.call('wget -q "'+source_doi+'" --user-agent="" --output-document=doi_'+timetag , shell=True) 
	doi_name='doi_'+str(timetag)
	return doi_name

## determines whether page is of Elsevier format
## based onregex patterns Elsevier pages have in common
def is_Elsevier(doi_name):
	rx=re.compile('sciencedirect',re.IGNORECASE)
	ry=re.compile('data-ln=',re.IGNORECASE)

	f=open(str(doi_name),'r')
	text=f.read()
	tempx = re.search(rx,text)
	tempy = re.search(ry, text)

	if tempx and not tempy:
		Elsevier=1
	elif tempx and tempy:
		Elsevier=2
	else:
		Elsevier=False
	f.seek(0)
	f.close()
	return Elsevier

## determines whether page is of Springer format
## based onregex patterns Springer pages have in common
def is_Springer(doi_name):
	rx=re.compile('spriner link|springerlink',re.IGNORECASE)
	f=open(str(doi_name),'r')
	text=f.read()
	temp = re.search(rx,text)
	if temp:
		Springer=True
	else:
		Springer=False
	f.seek(0)
	f.close()
	return Springer

## Grabs and cleans the author and email fields 
## for Elsevier-type formatting
def get_Elsevier(doi_name):
	infile=open(doi_name,'r')
	authors=[]
	emails=[]

	if is_Elsevier(doi_name)==1:
		for line in infile: #inf
			if 'citation_author"' in line:
				name=line.split('content=')[1].split('>')[0]
				authors.append(name.strip('"\''))
			if 'author email"' in line:
				email=line.split('author email">')[1].split('<')[0]
				emails.append(email.strip('"\''))

	elif is_Elsevier(doi_name)==2:
		text = infile.read()
		rx = re.compile('data-fn=.*data-pos')
		tempx = re.search(rx,text).group(0)
		auth_groups=tempx.split('data-fn=')

		for i in range(len(auth_groups)):
			ag=auth_groups[i]
			if ag !='':
				fn=ag.split('data-ln')[0]
				ln=ag.split('data-ln="')[1].split('data-pos')[0]
				full = fn.strip() + " " +ln.strip()
				chars = '"\':;&'
				for c in chars:
					full=full.replace(c,'').strip() #3 added skip chars
				authors.append(full)

		ry = re.compile('mailto:.*')#class="auth_mail"')
		tempy = re.search(ry,text).group(0)
		email_groups=tempy.split('mailto:')
		for j in range(len(email_groups)):
			eg=email_groups[j]
			if eg !='':
				email = eg.split('class=')[0]#.split("mailto:")[1]
				email = email.replace('"','').strip()
				emails.append(email)

	## assign empty strings to names without emails
	if len(authors) != len(emails):
		names=[]
		addr=[]		
		for i in range(len(authors)):
		 	names.append(authors[i])
		 	try:
		 		addr.append(emails[i])
		 	except IndexError:
		 		addr.append('')
	else:	
		names=authors
		addr=emails 			

	## associate name to email
	for j in range(len(names)):
		for k in range(len(addr)):
			if (names[j].split()[0].lower() or names[j].split()[1].lower() ) in addr[k].lower():
				temp=addr[j]
				addr[j]=addr[k] ## assign match to jth entry
				addr[k]=temp #addr[j]

	objectdict=dict(zip(names, addr))
	return objectdict

## Grabs and cleans the author and email fields 
## for Springer-type formatting
def get_Springer(doi_name): 
	infile=open(doi_name,'r')
	authors=[]
	emails=[]
	if is_Springer(doi_name):
		for line in infile: #inf
			if 'citation_author"' in line:
				name=line.split('content=')[1].split('/>')[0]
				chars = '"\':;&><'
				for c in chars:
					name=name.replace(c,'').strip()
				authors.append(name.strip('"\''))

			if 'citation_author_email"' in line:
				email=line.split('content=')[1].split('/>')[0]
				emails.append(email.strip('"\''))

	if len(authors) != len(emails):
		names=[]
		addr=[]		
		for i in range(len(authors)):
		 	names.append(authors[i])
		 	try:
		 		addr.append(emails[i])
		 	except IndexError:
		 		addr.append('')
	else:	
		names=authors
		addr=emails 			

	for j in range(len(names)):
		for k in range(len(addr)):
			if (names[j].split()[0].lower() or names[j].split()[1].lower() ) in addr[k].lower():
				temp=addr[j]
				addr[j]=addr[k] 
				addr[k]=temp
 
	objectdict=dict(zip(names, addr))
	return objectdict

## Takes get_[page type] function and the doi_name as args
## Returns empy string if get_[page type] does not apply
## to the input doi
def pull_authors_emails(get_fcn, doi_name):
	returnstring=''
	for i in range(len(get_fcn(doi_name))):
		key=list(get_fcn(doi_name).keys())[i].strip()
		val=list(get_fcn(doi_name).values())[i].strip()
		if val != '':
			returnstring=returnstring + " " +key+", "+ val+"\n"
		else:
			returnstring=returnstring + " " +key+" "+ val+"\n"
	return returnstring

## deletes locally stored html files after parsing
def remove_pages():
	subprocess.call("rm -r -f doi_* ", shell=True)
	return