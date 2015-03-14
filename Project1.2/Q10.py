#!/usr/bin/python

def DEBUG_1(str):
    if 0:
        print str

def DEBUG(str):
    if 1:
        print str

def max_consequtive_increasing_days(article_output):
    max_increasing_days = 0
    increasing_days = 0
    previous_day_view = 0

    sequence_start_index = 1
    curr_start = 1
    index = 1

    DEBUG_1("Article output " + article_output)
    line_list = article_output.split("\t")
    days = line_list[2:]

    for day in days:
        day_view = int(day.split(":")[1])

        DEBUG_1(str(previous_day_view) + " " + str(day_view) + " " + str(increasing_days) + " " + str(max_increasing_days))

        if day_view > previous_day_view:
            increasing_days += 1
        else:
            if increasing_days > max_increasing_days:
                max_increasing_days = increasing_days
                sequence_start_index = curr_start
            increasing_days = 1
            curr_start = index

        previous_day_view = day_view
        index += 1

    if increasing_days > max_increasing_days:
        max_increasing_days = increasing_days
        sequence_start_index = curr_start

    DEBUG_1("Return " + str(sequence_start_index) + " " + str(max_increasing_days))
    return sequence_start_index, max_increasing_days

output_f = open("output", "r")
#output_f = open("o", "r")


max_days = 0
articles_with_max = 0

for line in output_f:
    DEBUG_1("Line " + line)
    i, n = max_consequtive_increasing_days(line.strip())
    if n == max_days:
        articles_with_max += 1
        DEBUG("New article with max " + str(max_days) + " " + str(articles_with_max) + " " + str(i) + " " + line)
    if n > max_days:
        max_days = n
        articles_with_max = 1
        DEBUG("New max " + str(max_days) + " " + str(articles_with_max) + " " + str(i) + " " + line)

DEBUG("Final Output " + str(max_days) + " " + str(articles_with_max))
print str(articles_with_max)

