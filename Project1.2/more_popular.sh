#!/bin/bash

# Article names are passed as two parameter 
# and will be available in $1 and $2

# Get the line from output for the given article name
first=`awk -v pattern="^$1$"  ' $2 ~ pattern { print $0; }' output`

# Get the line from output for the given article name
second=`awk -v pattern="^$2$"  ' $2 ~ pattern { print $0; }' output`

line=`echo $first | tr "\t" " "`
#Set line as position parameters
set $line
#Skip first two fields
shift
shift

#Store the number of access per day in an array
args1=()
for val in $@
do
   num=`echo $val | cut -d':' -f2`
   args1+=("$num")
done


line=`echo $second | tr "\t" " "`
#Set line as position parameters
set $line
#Skip first two fields
shift
shift

#Store the number of access per day in an array
args2=()
for val in $@
do
   num=`echo $val | cut -d':' -f2`
   args2+=("$num")
done

#Find the number days article1 was more popular than article2
count=0
for (( i = 0; i < ${#args1[@]}; i++ ))
do
    if [ ${args1[$i]} -gt ${args2[$i]} ]
    then
        count=`expr $count + 1`
    fi
done

echo "$count"
