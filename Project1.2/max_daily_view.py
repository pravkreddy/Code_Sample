#!/usr/bin/python

import sys
import re

output_f = open("output", "r")

article_name = re.escape(sys.argv[1])
article_pattern = article_name + '$'

article_max_views = 0

for line in output_f:
    line.strip();
    line_list = line.split("\t")
    name = line_list[1].strip()
    if re.match(article_pattern, name) != None:
#	print line
        days = line_list[2:]
        for day in days:
            date, access = day.split(":")
            if article_max_views < int(access):
                article_max_views = int(access)
        break
print str(article_max_views) + " " + sys.argv[1]
