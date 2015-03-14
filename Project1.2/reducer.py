#!/usr/bin/python
import sys 
import re 

current_pgtitle = None
access=0
date=0
totalmonthaccess=0
intaccessval=0
my_dict=30*[0]

for line in sys.stdin:
	line=line.strip()
        
	try:
		pgtitle,value = line.split("\t")        
		date,access = value.split("_")	
		intaccessval=int(access)
		intdate=int(date[-2:])-1
		year=date[:6]
	except ValueError:
		continue	
	if intaccessval < 0:
		continue
	if intdate > 30 or intdate < 0:
		continue
	if current_pgtitle ==  None:
		current_pgtitle = pgtitle
		my_dict=30*[0]		
	if current_pgtitle == pgtitle:
		my_dict[intdate]= my_dict[intdate] + intaccessval
		totalmonthaccess += intaccessval					                 
	else:
		if current_pgtitle:
			if totalmonthaccess > 100000:
				sys.stdout.write(str(totalmonthaccess)+"\t"+current_pgtitle)
				for index in range(len(my_dict)):		
					if index < 9:	
						sys.stdout.write("\t"+year+"0"+str(index+1)+":"+str(my_dict[index]))
					else:
						sys.stdout.write("\t"+year+str(index+1)+":" + str(my_dict[index]))
				print 					
		my_dict=30*[0]
		current_pgtitle = pgtitle			
		totalmonthaccess = intaccessval
		my_dict[intdate]=intaccessval
				
if current_pgtitle:
	if totalmonthaccess > 100000:
        	sys.stdout.write(str(totalmonthaccess)+"\t"+current_pgtitle)
                for index in range(len(my_dict)):              
			if index < 9:	
				sys.stdout.write("\t"+year+"0"+ str(index+1)+":"+str(my_dict[index]))
                	else:
				sys.stdout.write("\t"+year+str(index+1)+":"+str(my_dict[index]))
		print
