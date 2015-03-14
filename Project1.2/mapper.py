#!/usr/bin/python
import sys
import re
import datetime
import os
include_str = 'en ([^a-z].*) (.+) .+$'
include = re.compile(include_str)

exclude_str = 'Media:|Special:|Talk:|User:|User_talk:|Project:|Project_talk:'
exclude_str += '|File:|File_talk:|Mediawiki:|Mediawiki_talk:'
exclude_str += '|Template:|Template_talk:|Category:|Category_talk:'
exclude_str += '|Help:|Help_talk:|Portal:|Wikipedia:|Wikipedia_talk:'
exclude = re.compile(exclude_str)

image_extn_str = '.*\.jpg$|.*\.gif$|.*\.png$|.*\.JPG$|.*\.GIF$|.*\.PNG$|.*\.txt$|.*\.ico$'
image_extn = re.compile(image_extn_str)

boilerplate_article_str = '404_error/$|Main_Page$|Hypertext_Transfer_Protocol$|Search$'
boilerplate_article = re.compile(boilerplate_article_str)

pg_title = None	

date=""
try:
	head,tail = os.path.split(os.environ["mapreduce_map_input_file"])
	date=tail.split('-')[1]                    
except KeyError:
	sys.exit()

for line in sys.stdin:
	line = line.strip()
	output = include.match(line)
	if output:
		pg_title = output.group(1)
		num_access = output.group(2)
		pg_title = pg_title.strip()
		num_access = num_access.strip()
		if exclude.match(pg_title) == None and \
		   image_extn.match(pg_title) == None and \
		   boilerplate_article.match(pg_title) == None:
        		print pg_title+"\t"+date+"_"+num_access

