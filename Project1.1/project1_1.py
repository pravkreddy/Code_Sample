#!/usr/bin/python

import re

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

parsed = [ ]

unfiltered_line_count = 0
unfiltered_num_requests = 0

filtered_line_count = 0
most_popular_views = 0
most_popular_article = ""

most_popular_movie_count = 0
most_popular_movie = ""

articles_with_10000_views = 0

with open("pagecounts-20141101-000000", "r") as file:
    for line in file:
    	unfiltered_line_count += 1
    	unfiltered_num_requests += int(line.split()[2])
        output = include.match(line)
        if output:
	    pg_title = output.group(1)
	    num_access = output.group(2)
	    if exclude.match(pg_title) == None and \
	       image_extn.match(pg_title) == None and \
	       boilerplate_article.match(pg_title) == None:
		
		filtered_line_count += 1
                parsed.append(pg_title + "\t" + num_access + "\n")
		if int(num_access) > most_popular_views:
		    most_popular_views = int(num_access)
		    most_popular_article = pg_title

		if re.match('.*\(film\).*', pg_title) and \
		   (most_popular_movie_count < int(num_access)): 
		    most_popular_movie_count = int(num_access)
		    most_popular_movie = pg_title

		if int(num_access) > 10000:
		    articles_with_10000_views += 1

print "Answer 2: Unfiltered num lines = " + str(unfiltered_line_count)
print "Answer 3: Unfiltered num requests = " + str(unfiltered_num_requests)
print "Answer 4: Filtered num lines = " + str(filtered_line_count)
print "Answer 5: Most Popular Article is \"" + most_popular_article + "\""
print "Answer 6: Number of views of most popular article = " + str(most_popular_views)
print "Most Popular Movie is \"" + most_popular_movie + "\""
print "Answer 7: Most Popular Movie count = " + str(most_popular_movie_count)
print "Answer 8: Number of articles with more than 10,000 views = " + str(articles_with_10000_views)

output = open("output", "w")
for line in parsed:
    output.write(line)
