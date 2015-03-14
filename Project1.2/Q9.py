#!/usr/bin/python

import sys
import re

output_f = open("output", "r")

max_total_view = 0
popular_article = ""

for line in output_f:
    line.strip();
    line_list = line.split("\t")

    total_view = int(line_list[0].strip())
    name = line_list[1].strip()
    views_on_nov1 = int(line_list[2].split(':')[1])

    if total_view > max_total_view and \
       views_on_nov1 == 0:
        max_total_view = total_view
        popular_article = name

if popular_article != "":
    print popular_article
