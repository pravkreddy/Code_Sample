#!/usr/bin/python
from boto.regioninfo import RegionInfo
from boto.ec2.autoscale import AutoScaleConnection
from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup
from boto.ec2.autoscale.tag import Tag
from boto.ec2.elb import ELBConnection
from boto.ec2.elb import HealthCheck
import boto.ec2.cloudwatch
from boto.ec2.autoscale import ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm
import requests
import time
import traceback
from lxml import html
import ConfigParser
import StringIO
import re

lgid = "i-42d8e9b3"
def DEBUG(str):
    if 1:
        print str
#-----------------------------------Creating a security group------------------------#
def create_security_group():
	conn = boto.ec2.connect_to_region('us-east-1')
	DEBUG("STEP 1:Creating Security group..")
	flag =0
	security_groups = conn.get_all_security_groups()
	for security_group in security_groups:    
	    if security_group.name == "security1":
	         flag =1
	         break
	if flag!=1:
	        # Create security group
	        myscgroup = conn.create_security_group('security1', 'Project 2.2')
	        myscgroup.authorize('tcp', 80, 80, '0.0.0.0/0')
	        myscgroup.authorize('tcp', 22, 22, '0.0.0.0/0')


#----------------------------------Create ELB( Elastic Load Balancer)------------------#
def create_elb():
	DEBUG("STEP 2:Creating Load Balancer..")
	try:
		conn = ELBConnection()	
		requiredzone = ['us-east-1a']
		requiredport = [(80, 80, 'http')]
		lb = conn.create_load_balancer('MyELB', requiredzone, requiredport)
		hc = HealthCheck(
			interval=20,
			healthy_threshold=3,
			unhealthy_threshold=5,
			target='HTTP:80/heartbeat'
			)
		lb.configure_health_check(hc)
		DEBUG("Load balancer(DNS) " + "= " + lb.dns_name)
		return lb.dns_name
	except:
		DEBUG("STEP 2:Exception Occured")
		traceback.print_exc()
		

def create_lc_as_su_sd_alarm():
#------------------------------------------Create LC( Launch Configuration)------------------------------------------#
	DEBUG("STEP 3:Creating Launch Configuration..")
	asconn = AutoScaleConnection()
	try:
		
		lc = LaunchConfiguration(name='P22LaunchConfig', image_id='ami-7c0a4614',
		                             key_name='project',
		                             instance_type='m3.medium',
		                             instance_monitoring=True,
		                             security_groups=['security1'])		
		asconn.create_launch_configuration(lc)
		DEBUG("STEP 3Launch Config created" +"= " +lc.name)
	except:
		DEBUG("STEP 3:Exception Occured")
		traceback.print_exc()
	
	#------------------------------------------Auto Scaling Creation----------------------------------------------------#
	DEBUG("STEP 4:Creating Auto Scaling Group..")
	try:		
		requiredzone = ['us-east-1a']
		
		project_tag = Tag(key='Project',value = '2.2',propagate_at_launch=True,resource_id="P22ASG")
		dc_tag = Tag(key='Name',value = 'Data Center',propagate_at_launch=True,resource_id="P22ASG")	
		ag = AutoScalingGroup(group_name='P22ASG', load_balancers=['MyELB'], launch_config='P22LaunchConfig', 
			                          availability_zones=requiredzone, min_size=1, desired_capacity=2, max_size=2,
						  tags=[project_tag, dc_tag])
		asconn.create_auto_scaling_group(ag)
		#asconn.create_or_update_tags([project_tag, dc_tag])
		DEBUG("STEP 4:P22ASG Name ="+ag.name)
	except:		
		DEBUG("STEP 4:Exception Occured")
		traceback.print_exc()
	#-----------------------------------------Scale Policy---------------------------------------------------------------#
	DEBUG("STEP 5:Creating Scale Out/In Policy..")
	try:
		scale_up_policy = ScalingPolicy(
			name='scale_up', adjustment_type='ChangeInCapacity',
			as_name='P22ASG', scaling_adjustment=1, cooldown=180)
		scale_down_policy = ScalingPolicy(
			name='scale_down', adjustment_type='ChangeInCapacity',
			as_name='P22ASG', scaling_adjustment=-1, cooldown=180)
		asconn.create_scaling_policy(scale_up_policy)
		asconn.create_scaling_policy(scale_down_policy)
		scale_up_policy = asconn.get_all_policies(
			    as_group='P22ASG', policy_names=['scale_up'])[0]
		scale_down_policy = asconn.get_all_policies(
			    as_group='P22ASG', policy_names=['scale_down'])[0]
	except:		
		DEBUG("STEP 5:Exception Occured")
		traceback.print_exc()
	#------------------------------------------Alarm-----------------------------------------------------------------------#
	DEBUG("STEP 6:Creating Alarm..")
	try:
		cloudwatch = boto.ec2.cloudwatch.connect_to_region('us-east-1')
		alarm_dimensions = {"AutoScalingGroupName": 'P22ASG'}
		scale_up_alarm = MetricAlarm(
			    name='scale_up_on_cpu', namespace='AWS/EC2',
			    metric='CPUUtilization', statistic='Average',
			    comparison='>', threshold='70',
			    period='60', evaluation_periods=2,
			    alarm_actions=[scale_up_policy.policy_arn],
			    dimensions=alarm_dimensions)
		cloudwatch.create_alarm(scale_up_alarm)
		scale_down_alarm = MetricAlarm(
			    name='scale_down_on_cpu', namespace='AWS/EC2',
			    metric='CPUUtilization', statistic='Average',
			    comparison='<', threshold='40',
			    period='60', evaluation_periods=2,
			    alarm_actions=[scale_down_policy.policy_arn],
			    dimensions=alarm_dimensions)
		cloudwatch.create_alarm(scale_down_alarm)
	except:		
		DEBUG("STEP 6:Exception Occured")
		traceback.print_exc()

def check_for_loadgenerator_ready():
	while True:
		reserv = boto.ec2.connect_to_region('us-east-1').get_all_instances(instance_ids=[lgid])
		instance = [r.instances[0] for r in reserv][0]
		try:		
			if not instance.public_dns_name:
				raise Exception("empty")
			url = "http://" + instance.public_dns_name 
		        while True:
				try:
			            response = requests.get(url, timeout=10)
			            if response.status_code == requests.codes.ok:
				       	    DEBUG("LG: Is ready!")
					    DEBUG(response.url)
		    			    DEBUG(response.text)
				       	    break
				    DEBUG(response.url)
				    DEBUG(response.text)
				    time.sleep(10)
				except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
				    print("Exception occurred. Retrying...")
				    traceback.print_exc()
				    continue
		except:
			traceback.print_exc()
			time.sleep(10)
			continue
		return instance.public_dns_name 

# Parse the HTTP GET Response and ensure the Data Center
# instance was "launched"
# Return a valid log URL parsed from response
# Return None otherwise
def get_log_url(html_response):
    tree = html.fromstring(html_response.text)
    body = tree.xpath('//body/text()')[0]
    print("########################CT:" +body)
    log_url = None
    if re.match(' launched.$', body, re.IGNORECASE) or re.match(' running.$',body,re.IGNORECASE):
    	log_url = tree.xpath('//a/@href')[0]

    print"################URL 1=" + log_url
    return log_url

# Start the LG Horizontal Scaling Test by issuing a 
# HTTP GET Request with the first Data center instance DNS name
# Return the HTTP GET response back to the caller
def try_start_test(load, elb,var):
    loader='http://'+lg_dns+var
    payload = {'dns': elb}
    while True:
        try:
    	    response = requests.get(loader, params=payload, timeout=10)
	    break
	except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
	    print("Exception occurred. Retrying...")
	    continue
    return response

def start_test(load, elb,var):
    log_url = None
    while True:
	response = try_start_test(load, elb,var)
	print "Response code " + str(response.status_code)
	#if response.status_code == requests.codes.ok:
	if response.text:
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

# Parse the LG log contents and check whether the target RPS was met
# Look for the last minute RPS values and calculate the sum
# Return True if sum meets RPS target, False otherwise
def parser(log_str):
    buf = StringIO.StringIO(log_str)
    config = ConfigParser.ConfigParser()
    config.readfp(buf)
    
    print buf
    return False
    
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
    val = response.text.find("Test finished")
    print "################## val = " + str(val)
    return val > 0

######################################################################################################
#------------------------------------------Main code-------------------------------------------------#
######################################################################################################       
create_security_group()
elb_dns=create_elb()
create_lc_as_su_sd_alarm()

lg_dns=check_for_loadgenerator_ready()

#start_warmup(lg_dns,elb_dns)	

#-------------------------------Satart Test------------------------------------------------------------#				
		
warmup_count = 1
while True:
    if warmup_count:
	log_url = start_test(lg_dns,elb_dns,'/warmup')
	while True:
		if target_rps_reached(lg_dns, log_url):
			print("Warm up :" + str(warmup_count) +"Completed")
			warmup_count -= 1
			break
		else:
			time.sleep(180)
		
start_test(lg_dns,elb_dns,'/junior')
while True:
	if target_rps_reached(lg_dns, log_url):
		print("Junior Test : Completed")
		break
	else:
		time.sleep(180)				
