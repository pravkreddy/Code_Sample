#!/usr/bin/python

import sys
import re

output_f = open("output", "r")

article_name = re.escape(sys.argv[1])
article_pattern = article_name + '$'

for line in output_f:
    line.strip();
    line_list = line.split("\t")
    name = line_list[1].strip()
    if re.match(article_pattern, name) != None:
	print line_list[0] + " " + sys.argv[1]
	break
