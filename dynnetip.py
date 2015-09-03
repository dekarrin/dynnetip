# Set the domain -> ip mapping with namecheap
import socket
import os
import os.path
import urllib2
import datetime

import configuration

def change_record(ip):
	get_req = configuration.ddns_submit_url
	get_req += '?host=' + configuration.ddns_host
	get_req += '&domain=' + configuration.ddns_domain
	get_req += '&password=' + configuration.ddns_password
	get_req += '&ip=' + ip
	response = urllib2.urlopen(get_req)
	return parse_change_response(response)

def parse_change_response(response):
	text = response.read()
	success = False
	new_ip = ''
	if (text.find('<ErrCount>0</ErrCount>') > -1):
		success = True
		ip_tag_start = text.find('<IP>')
		ip_tag_end = text.find('</IP>')
		if ip_tag_start != -1 and ip_tag_end != -1:
			new_ip_start = ip_tag_start + 4
			new_ip_end = ip_tag_end
			new_ip = text[new_ip_start:new_ip_end]
	return {'success': success, 'ip': new_ip, 'response': text}
			
	
def get_current_ip():
	response = urllib2.urlopen(configuration.current_ip_url)
	ip = response.read()
	return ip.strip()
	
def read_local_ip_record(cache_file):
	if not os.path.isfile(cache_file):
		return None
	cache = open(cache_file, 'r')
	ip = cache.read()
	cache.close()
	return ip.strip()
	
def write_local_ip_record(cache_file, ip):
	cache = open(cache_file, 'w')
	cache.write(ip.strip())
	cache.close()
	
def check_log_size():
	if os.path.isfile(configuration.log_file_path):
		cur_log_bytes = os.stat(configuration.log_file_path).st_size
		while cur_log_bytes > configuration.log_file_max_size * 1024 * 1024:
			logf = open(configuration.log_file_path, 'r')
			lines = logf.readlines()
			logf.close()
			logf = open(configuration.log_file_path, 'w')
			for l in lines[1:]:
				logf.write(l)
			logf.close()
			cur_log_bytes = os.stat(configuration.log_file_path).st_size
	
def log(msg):
	cur_time = datetime.datetime.now().isoformat()
	check_log_size()
	log_file = open(configuration.log_file_path, 'a')
	log_file.write(cur_time + " " + msg + "\n")
	log_file.close()
	
import sys
def update_dns():
	old_ip_addr = read_local_ip_record(configuration.cache_file_path)
	try:
		cur_ip_addr = get_current_ip()
	except urllib2.URLError:
		log('Could not establish inet connection to check IP')
		return
	if cur_ip_addr != old_ip_addr:
		try:
			result = change_record(cur_ip_addr)
		except urllib2.URLError:
			log('Could not establish inet connection to update DNS')
			return
		if result['success']:
			ip = result['ip']
			if ip == '':
				 ip = cur_ip_addr
			write_local_ip_record(configuration.cache_file_path, ip)
			log('DNS updated to ' + ip.strip())
		else:
			log('DNS update failed. Response: ' + result['response'])
	else:
		log("IP checked - no change")

if __name__ == "__main__":
	update_dns()
