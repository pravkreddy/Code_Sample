#!/usr/bin/python
import sys
import re

output_f = open("output", "r")

line_list =[]
dict={}
article_name = re.escape(sys.argv[1])
article_pattern = article_name + '$'

for line in output_f:
    line.strip();
    line_list = line.split("\t")

    name = line_list[1].strip()
    if re.match(article_pattern, name) != None:
        slist=line_list[2:]
        for index in range(len(slist)):
                value= slist[index]
                year,count = value.split(":")
                dict[year]=int(count)
        print max(dict, key=dict.get)
