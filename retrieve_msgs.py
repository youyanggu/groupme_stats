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
parser.add_argument('-d', '--dm', help='Retrieve all direct messages', action="store_true")
parser.add_argument('-g', '--group', help='Name of group to retrieve. Run without this flag to see list of groups.')
parser.add_argument('-c', '--csv', help='Name of csv file to write to.', default='temp.csv')
parser.add_argument('-o', '--overwrite', help='overwrite csv file', action="store_true")

URL = 'https://api.groupme.com/v3'
TOKEN = None

########## STAT FUNCTIONS ##########

def getNumFavorited(msg):
	"""Counts the number of favorites the mssage received."""
	num_favorited = msg['favorited_by']
	return len(num_favorited)

####################################


##########################
#
# GROUPME API Helper Functions
#
##########################

def get(response):
	"""Retrieve the 'response' portion of the json object."""
	return response.json()['response']

def getDMs():
	"""Returns a dictionary with direct messages."""
	params = {'per_page' : 100}
	groups = get(requests.get(URL + '/chats' + TOKEN, params=params))
	if groups is None:
		return None
	d = {}
	for group in groups:
		name = str(group['other_user']['name'].encode('utf-8').strip())
		count = group['messages_count']
		if count > 0:
			d[name] = {}
			d[name]['id'] = group['other_user']['id']
			d[name]['count'] = count
	return d

def getGroups():
	"""
	Returns a dictionary with group names as keys and a dictionary of
	group id and # of messages as values

	"""
	params = {'per_page' : 100}
	groups = get(requests.get(URL + '/groups' + TOKEN, params=params))
	if groups is None:
		return None
	d = {}
	for group in groups:
		name = group['name'].encode('utf-8').strip()
		count = group['messages']['count']
		if count > 0:
			d[name] = {}
			d[name]['id'] = group['group_id']
			d[name]['count'] = count
	return d

def getGroup(group_id, direct_msgs=False):
	if direct_msgs:
		params = {'other_user_id' : group_id}
		group = get(requests.get(URL + '/direct_messages' + TOKEN, params=params))
	else:
		group = get(requests.get(URL + '/groups/' + group_id + TOKEN))
	return group

def getGroupName(group_id, direct_msgs):
	group = getGroup(group_id, direct_msgs)
	if direct_msgs:
		return group_id
	else:
		return str(group['name'])

def getGroupCount(group_id, direct_msgs):
	group = getGroup(group_id, direct_msgs)
	if direct_msgs:
		return int(group['count'])
	else:
		return int(group['messages']['count'])

def getGroupNames(groups):
	return groups.keys()

def sortByCount(groups):
	arr = []
	for key in groups:
		arr.append((key, groups[key]['count']))
	return sorted(arr, key=lambda k: k[1], reverse=True)

def getLastMsgId(group_id, direct_msgs):
	group = getGroup(group_id, direct_msgs)
	if direct_msgs:
		return group['direct_messages'][0]['id']
	else:
		return group['messages']['last_message_id']

def getMessages(group_id, direct_msgs, before_id=None, since_id=None):
	"""
	Given the group_id and the message_id, retrieves 20 messages

	Params:
	before_id: take the 20 messages before this message_id
	since_id: take the 20 messages after this message_id (maybe)
	"""
	params = {}
	if before_id is not None:
		params['before_id'] = str(before_id)
	if since_id is not None:
		params['since_id'] = str(since_id)
	try:
		if direct_msgs:
			params['other_user_id'] = group_id
			msgs = get(requests.get(URL + '/direct_messages' + TOKEN, params=params))
		else:
			msgs = get(requests.get(URL + '/groups/' + group_id + '/messages' + TOKEN, params=params))

	except ValueError:
		return []
	return msgs

def countMsgs(group_name, group_id, direct_msgs, csv_file=None, processTextFunc=None, sinceTs=None):
	"""
	Function that calls GroupMe API and processes messages of a particular group.

	Params:
	group_id: group_id of group
	csv_file: name of output csv file
	processTextFunc: a function that processes a msg and returns a value that is appended to user data
	sinceTs: only process messages after this timestamp
	"""
	if csv_file:
		f = open(csv_file, "ab")
		wr = csv.writer(f, dialect="excel")
	if type(sinceTs) == datetime.datetime:
		sinceTs = int(sinceTs.strftime("%s"))
	totalCount = getGroupCount(group_id, direct_msgs)
	print "Counting messages for {} (Total: {})".format(group_name, totalCount)
	curCount = 0
	users = {}
	lastMsgId = str(int(getLastMsgId(group_id, direct_msgs))+1) # get current msg as well
	while (curCount < totalCount):
		if curCount % 100 == 0:
			print curCount
		msgs = getMessages(group_id, direct_msgs, lastMsgId)
		if not msgs:
			break
		if direct_msgs:
			msgs = msgs['direct_messages']
		else:
			msgs = msgs['messages']
		if not msgs:
			break
		for msg in msgs:
			if msg['created_at'] < sinceTs:
				return curCount, users
			curCount += 1
			try:
				created_at = datetime.datetime.fromtimestamp(msg['created_at']).strftime('%Y-%m-%d %H:%M:%S')
			except:
				print "Error parsing created_at"
				created_at = ""
			user = msg['name']
			text = msg['text']
			likes = getNumFavorited(msg)
			if text is None:
				text = ""
			if user is None:
				user = ""
			if created_at is None:
				created_at = ""
			if user not in users:
				users[user] = []
			if csv_file:
				wr.writerow([group_name, created_at.encode('utf-8'), user.encode('utf-8'), text.encode('utf-8'), likes])
			if processTextFunc is not None:
				data = processTextFunc(msg)
				users[user].append(data)
		lastMsgId = msgs[-1]['id']
	if csv_file:
		f.close()
	return curCount, users

def main(retrieve_all, direct_msgs, group_name, csv_file, overwrite):
	if direct_msgs:
		groups = getDMs()
	else:
		groups = getGroups()
	if groups is None:
		raise RuntimeError("Cannot retrieve groups. Is your token correct?")

	if retrieve_all:
		for k, v in groups.iteritems():
			new_csv_file = k.lower().replace(' ', '_')+'.csv' if not csv_file else csv_file
			count, _ = countMsgs(k, v['id'], direct_msgs, csv_file=new_csv_file)
			print "Processed {} messages. Wrote to {}.".format(count, csv_file)
	elif group_name:
		if group_name not in groups:
			print "Group name not found. Here are the list of groups:"
			print getGroupNames(groups)
		else:
			if csv_file and os.path.isfile(csv_file) and not overwrite:
				raise IOError("File already exists. Try setting --overwrite.")
			if not csv_file:
				csv_file = group_name.lower().replace(' ', '_')+'.csv'
			count, _ = countMsgs(group_name, groups[group_name]['id'], direct_msgs, csv_file=csv_file)
			print "Processed {} messages. Wrote to {}.".format(count, csv_file)
	else:
		sorted_groups = sortByCount(groups)
		print "Here is all the groups and their message counts:"
		print sorted_groups

if __name__ == "__main__":
	args = parser.parse_args()
	token = args.token
	if len(token) not in [32, 40]:
		raise IOError("Invalid token. Please enter a 32-char or 40-char string.")
	TOKEN = "?token=" + token

	main(args.all, args.dm, args.group, args.csv, args.overwrite)


