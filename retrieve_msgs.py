""" 
@author: youyanggu

Tool to retrieve GroupMe messages using the GroupMe API and output them to a CSV file.

"""

import json
import requests
import datetime
import csv
import argparse
import os

parser = argparse.ArgumentParser(description='Tool to retrieve GroupMe messages and output them to a CSV file.')
parser.add_argument('token', help='Access token used to authenticate yourself when making API requests.')
parser.add_argument('-a', '--all', help='Retrieve all groups', action="store_true")
parser.add_argument('-g', '--group', help='Name of group to retrieve. Run without this flag to see list of groups.')
parser.add_argument('-c', '--csv', help='Name of csv file to write to.')
parser.add_argument('-o', '--overwrite', help='overwrite csv file', action="store_true")

URL = 'https://api.groupme.com/v3'
TOKEN = None

########## STAT FUNCTIONS ##########

""" Counts the number of favorites the mssage received """
def getNumFavorited(msg):
	num_favorited = msg['favorited_by']
	return len(num_favorited)

####################################

	
##########################
#
# GROUPME API Helper Functions
# 
##########################

""" Retrieve the 'response' portion of the json object """
def get(response):
	return response.json()['response']

""" 
Returns a dictionary with group names as keys and a dictionary of 
group id and # of messages as values 

"""
def getGroups():
	params = {'per_page' : 100}
	groups = get(requests.get(URL + '/groups/' + TOKEN, params=params))
	if groups is None:
		return None
	d = {}
	for group in groups:
		name = str(group['name'])
		count = group['messages']['count']
		if count > 0:
			d[name] = {}
			d[name]['id'] = group['group_id']
			d[name]['count'] = count
	return d

def getGroup(group_id):
	group = get(requests.get(URL + '/groups/' + group_id + TOKEN))
	return group

def getGroupName(group_id):
	group = getGroup(group_id)
	return str(group['name'])

def getGroupCount(group_id):
	group = getGroup(group_id)
	return int(group['messages']['count'])

def getGroupNames(groups):
	return [group['name'] for group in groups]

def sortByCount(groups):
	arr = []
	for key in groups:
		arr.append((key, groups[key]['count']))
	return sorted(arr, key=lambda k: k[1], reverse=True)

def getLastMsgId(group_id):
	return getGroup(group_id)['messages']['last_message_id']

""" 
Given the group_id and the message_id, retrieves 20 messages

Params:
before_id: take the 20 messages before this message_id
since_id: take the 20 messages after this message_id (maybe)
"""
def getMessages(group_id, before_id=None, since_id=None):
	params = {}
	if before_id is not None:
		params['before_id'] = str(before_id)
	if since_id is not None:
		params['since_id'] = str(since_id)
	msgs = get(requests.get(URL + '/groups/' + group_id + '/messages' + TOKEN, params=params))
	return msgs

##########################


"""
Function that calls GroupMe API and processes messages of a particular group.

Params:
group_id: group_id of group
csv_file: name of output csv file
processTextFunc: a function that processes a msg and returns a value that is appended to user data
sinceTs: only process messages after this timestamp
"""
def countMsgs(group_id, csv_file=None, processTextFunc=None, sinceTs=None):
	if csv_file:
		f = open(csv_file, "wb")
		wr = csv.writer(f, dialect="excel")
	if type(sinceTs) == datetime.datetime:
		sinceTs = int(sinceTs.strftime("%s"))
	totalCount = getGroupCount(group_id)
	print "Counting messages for", getGroupName(group_id), "( out of", totalCount, ")"
	curCount = 0
	users = {}
	lastMsgId = str(int(getLastMsgId(group_id))+1) # get current msg as well
	while (curCount < totalCount):
		if curCount % 100 == 0:
			print curCount
		msgs = getMessages(group_id, lastMsgId)
		for msg in msgs['messages']:
			if msg['created_at'] < sinceTs:
				return users
			curCount += 1
			created_at = datetime.datetime.fromtimestamp(msg['created_at']).strftime('%Y-%m-%d %H:%M:%S')
			user = msg['name']
			text = msg['text']
			if text is None:
				text == ""
			if user not in users:
				users[user] = []
			if csv_file:
				wr.writerow([created_at.encode('utf-8'), user.encode('utf-8'), text.encode('utf-8')])
			if processTextFunc is not None:
				data = processTextFunc(msg)
				users[user].append(data)
		lastMsgId = msgs['messages'][-1]['id']
	return curCount, users

def main(retrieve_all, group, csv_file, overwrite):
	groups = getGroups()
	if groups is None:
		raise RuntimeError("Cannot retrieve groups. Is your token correct?")
		
	if retrieve_all:
		for k, v in groups.iteritems():
			csv_file = k+'.csv'
			count, _ = countMsgs(v['id'], csv_file=csv_file)
			print "Processed {} messages. Wrote to {}.".format(count, csv_file)
	elif group:
		if group not in groups:
			print "Group name not found. Here are the list of groups:"
			print getGroupNames(groups)
		else:
			if csv_file and os.path.isfile(csv_file) and not overwrite:
				raise IOError("File already exists. Try setting --overwrite.")
			count, _ = countMsgs(groups[group]['id'], csv_file=csv_file)
			print "Processed {} messages. Wrote to {}.".format(count, csv_file)
	else:
		sorted_groups = sortByCount(groups)
		print "Here is all the groups and their message counts:"
		print sorted_groups

if __name__ == "__main__":
	args = parser.parse_args()
	token = args.token
	if len(token) != 32:
		raise IOError("Invalid token. Please enter a 32-char string.")
	TOKEN = "?token=" + token

	main(args.all, args.group, args.csv, args.overwrite)


