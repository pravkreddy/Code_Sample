#!/usr/bin/python

import boto.ec2
import time
import requests
import StringIO
import ConfigParser
import re
from lxml import html

# Return the name of a provisioned instance
# Waits for the instance status to be running and have an assigned DNS name
# Handle the case where an instance takes too long to come up by gracefully 
# giving up and letting the caller retry
def get_instance_name(instance):
    try_count = 0
    while True :
	try:
            time.sleep(10)
            status = instance.update()

            if status =='running' and instance.public_dns_name != None :
                print "New Instance " + instance.id + " accessible at " + instance.public_dns_name
		break

            print("Instance status:"+ status)
	    try_count += 1
	    if try_count > 5:
		print("Too many retries, giving up...")
		conn.terminate_instances(instance_ids=[instance.id])
		return None
	except boto.exception.EC2ResponseError as e:
	    # instance.update API can throw an exception if the instance-id is not found
	    # Lets retry as it might take sometime for the provisioned instance to be accessibly by AWS
	    print("Exception occurred. Retrying...")
	    continue
		
    return instance.public_dns_name

# Create a Load Generator instance and return the name if successful
# On failure, None is returned and the caller must retry
def try_create_loadgenerator():
    reservation=conn.run_instances(
            'ami-4c4e0f24',
            key_name='project',
            instance_type='m1.medium',
            security_groups=['security2'])

    instance = reservation.instances[0]

    print("Load generator starting..")
    name = get_instance_name(instance)

    instance.add_tag("LoadGenerator", "Project")
    instance.add_tag("Project", "2.1")

    return name

# Create Load Generator instance
def create_loadgenerator():
    name = None
    while name == None:
	name = try_create_loadgenerator()
    return name

# Wait till the DC is ready
# DC is ready when we can successfully issue a HTTP GET 
# request for the track/device URL
def wait_till_datacenter_is_ready(datacenter):
    url = "http://" + datacenter + "/track/device"
    while True:
	try:
	    time.sleep(10)
	    print("Waiting for Datacenter to be ready!")
            response = requests.get(url, timeout=10)
            if response.status_code == requests.codes.ok:
	        print("Datacenter is now ready!")
		print(response.url)
		print(response.text)
	        break
	    print(response.url)
	    print(response.text)
	except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
	    print("Exception occurred. Retrying...")
	    continue

# Create a Data Center isntance and return the name if successful
# On failure, None is returned and the caller must retry
def try_create_datacenter():
    reservation=conn.run_instances(
            'ami-b04106d8',
            key_name='project',
            instance_type='m1.medium',
            security_groups=['security2'])

    print("Reservation size " + str(len(reservation.instances)))
    instance=reservation.instances[0]

    print('Data Instance starting...')
    name = get_instance_name(instance)

    instance.add_tag("DataCenter", "Project")
    instance.add_tag("Project", "2.1")

    return name

# Create Data Center instance
def create_datacenter():
    name = None
    while name == None:
	name = try_create_datacenter()
    wait_till_datacenter_is_ready(name)
    return name

# Issue a HTTP GET request to capture and parse
# the LG log and return true if the Target RPS of 4000 is met
# Return false otherwise
def target_rps_reached(load, log_url):
    loader="http://" + load + log_url
    while True:
        try:
            response = requests.get(loader, timeout=10)
	    break
	except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
	    print("Exception occurred. Retrying...")
	    continue

    return parser(response.text)

# Parse the HTTP GET Response and ensure the Data Center
# instance was "launched"
# Return a valid log URL parsed from response
# Return None otherwise
def get_log_url(html_response):
    tree = html.fromstring(html_response.text)
    body = tree.xpath('//body/text()')[0]

    log_url = None
    if re.match(' launched.$', body, re.IGNORECASE):
    	log_url = tree.xpath('//a/@href')[0]

    return log_url

# Start the LG Horizontal Scaling Test by issuing a 
# HTTP GET Request with the first Data center instance DNS name
# Return the HTTP GET response back to the caller
def try_start_test(load, datacenter):
    loader="http://"+load+"/test/horizontal"
    payload = {'dns': datacenter}
    while True:
        try:
    	    response = requests.get(loader, params=payload, timeout=10)
	    break
	except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
	    print("Exception occurred. Retrying...")
	    continue

    return response

# Start the LG Horizontal Scaling Test
# If a failure occurs due to an Error in HTTP GET 
# or we dint get the "Test launched" message in the response content, 
# retry starting the test (until successful)
# Return the log_url to the caller
def start_test(load, datacenter):
    log_url = None
    while True:
	response = try_start_test(load, datacenter)
	print "Response code " + str(response.status_code)
	if response.status_code == requests.codes.ok:
    	    log_url = get_log_url(response)
	    if log_url != None:
	    	break
	print(response.url)
	print(response.text)
	print("Starting test failed. Sleeping 30secs before retrying...")
	time.sleep(30)

    print(response.url)
    print(response.text)
    print("Test Started")
    return log_url

# Add a DC to the currently running LG Horizontal Scaling Test by issuing a 
# HTTP GET Request with the Data center instance DNS name
# Return the HTTP GET response back to the caller
def try_add_dc(load, datacenter):
    loader="http://"+load+"/test/horizontal/add"
    payload = {'dns': datacenter}
    print("Posting Get request to add DC to LG")
    while True:
	try:
    	    response = requests.get(loader, params=payload, timeout=10)
	    break
	except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
	    print("Exception occurred. Retrying...")
	    continue

    return response

# Parse the HTTP GET Response and ensure the Data Center
# instance was added to the test and return True
# Return False otherwise
def check_add_dc_result(response):
    if response.status_code != requests.codes.ok:
	return False

    tree = html.fromstring(response.text)
    body = tree.xpath('//body/text()')[0]

    if re.match('Data Center is added', body, re.IGNORECASE):
	return True

    return False
 
# Add a DC to the currently running LG Horizontal Scaling Test
# If a failure occurs due to an Error in HTTP GET 
# or we dint get the "Data Center is added" message in the response content, 
# retry adding DC to the test (until successful)
def add_dc_to_test(load,datacenter):
    while True:
	response = try_add_dc(load, datacenter)
	if check_add_dc_result(response):
	    break
	print(response.url)
	print(response.text)
	print("Adding DC to test failed. Sleeping 30secs before retrying...")
	time.sleep(30)

    print("DC added to Test")
    print(response.url)
    print(response.text)

# Parse the LG log contents and check whether the target RPS was met
# Look for the last minute RPS values and calculate the sum
# Return True if sum meets RPS target, False otherwise
def parser(log_str):
    buf = StringIO.StringIO(log_str)
    config = ConfigParser.ConfigParser()
    config.readfp(buf)
    
    total = 0
    val = 0
    for section in reversed(config.sections()):
        if re.match('Minute ', section):
	    for option in config.options(section):
	        try:
		    val = config.getfloat(section, option)
		    total += val
	        except ValueError:
		    continue
	    break

    print("Sum is " + str(total))
    return total >= 4000

#Main code                     
conn = boto.ec2.connect_to_region("us-east-1",
       aws_access_key_id='',
       aws_secret_access_key='')
flag = 0
security_groups = conn.get_all_security_groups()
for security_group in security_groups:
    if security_group.name == "security2":
         flag = 1
         break
if flag != 1:
        # Create security group
        myscgroup = conn.create_security_group('security2', 'Project 2.1')
        myscgroup.authorize('tcp', 80, 80, '0.0.0.0/0')
        myscgroup.authorize('tcp', 22, 22, '0.0.0.0/0')

load = create_loadgenerator()
datacenter = create_datacenter()
log_url = start_test(load, datacenter)

while True:
    print("Sleeping for 3mins...")
    time.sleep(180)
    if target_rps_reached(load, log_url):
	print("Target reached. Exiting...")
	break;
    datacenter = create_datacenter()
    add_dc_to_test(load, datacenter)
