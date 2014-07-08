import json
import requests
import datetime

url = 'https://api.groupme.com/v3'
token = '?token=904f53d0e88801316f9a729b72f3445b'

def get(response):
	return response.json()['response']

def getGroups():
	params = {'per_page' : 100}
	groups = get(requests.get(url + '/groups/' + token, params=params))
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
	group = get(requests.get(url + '/groups/' + group_id + token))
	return group

def getGroupName(group_id):
	group = getGroup(group_id)
	return str(group['name'])

def getGroupCount(group_id):
	group = getGroup(group_id)
	return int(group['messages']['count'])

def sortByCount(groups):
	arr = []
	for key in groups:
		arr.append((key, groups[key]['count']))
	return sorted(arr, key=lambda k: k[1], reverse=True)

# returns 20 messages
def getMessages(group_id, before_id=None, since_id=None):
	params = {}
	if before_id is not None:
		params['before_id'] = str(before_id)
	if since_id is not None:
		params['since_id'] = str(since_id)
	msgs = get(requests.get(url + '/groups/' + group_id + '/messages' + token, params=params))
	return msgs

def getLastMsgId(group_id):
	return getGroup(group_id)['messages']['last_message_id']

########## STAT FUNCTIONS ##########
def getStrLen(msg):
	text = msg['text']
	if text is None:
		return 0
	else:
		return len(text)

def getNumFavorited(msg):
	num_favorited = msg['favorited_by']
	return len(num_favorited)
####################################

def getStats(data, ignoreGroupMe=True, total=False):
	l = []
	num_people = total_msgs = total_data_per_person = total_data = 0
	for k,v in data.iteritems():
		if ignoreGroupMe and str(k) == 'GroupMe':
			continue
		num_people += 1
		num_msgs = len(v)
		total_msgs += num_msgs
		total_data_per_person = sum(v)
		total_data += total_data_per_person
		if total:
			l.append((str(k), num_msgs, total_data_per_person))
		else:
			avg_data_len = 0
			if num_msgs != 0:
				avg_data_len = round(sum(v)*1.0 / num_msgs, 1)
			l.append((str(k), num_msgs, avg_data_len))
	l = sorted(l, key=lambda k:k[1], reverse=True)
	if total:
		l.append(('Average', round(total_msgs * 1.0 / num_people, 1), round(total_data * 1.0 / num_people, 1)))
		l.append(('Total', total_msgs, total_data))
	else:
		l.append(('Average', round(total_msgs * 1.0 / num_people, 1), round(total_data * 1.0 / total_msgs, 1)))
		l.append(('Total', total_msgs))
	return l

def countMsgs(group_id, processTextFunc=getStrLen, sinceTs=None):
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
			user = msg['name']
			if user not in users:
				users[user] = []
			else:
				data = processTextFunc(msg)
				users[user].append(data)
		lastMsgId = msgs['messages'][-1]['id']
	return users

groups = getGroups()
sorted_groups = sortByCount(groups)
bball_id = groups['Bball']['id']
traders_id = groups['Traders']['id']
tx_id = groups['TXec \'13-\'14']['id']

#dt = datetime.datetime(2014, 5, 23)
#bball_data_since = countMsgs(bball_id, sinceTs=dt)
traders_data = countMsgs(traders_id, getNumFavorited)
tx_data = countMsgs(tx_id, getNumFavorited)

#for data in [data_since, traders_data, tx_data]:
#	print getStats(data)



