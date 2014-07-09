import json
import requests
import datetime
import csv

url = 'https://api.groupme.com/v3'


def getOccurances(word, once=True, print_matches=False, match_exactly=False, print_user=None):
	def getNum(user, original_text):
		count = 0
		if original_text is None:
			return 0
		else:
			text = original_text.lower()
			if type(word) == list:
				for w in word:
					if match_exactly:
						if text == w: count = 1
					else:
						count += text.count(w)
			else:
				if match_exactly:
					if word == text: count = 1
				else:
					count = text.count(word)
			if print_matches and count > 0:
				if print_user is None or print_user == user:
					print user, ':', original_text
			if once:
				return min(count, 1)
			else:
				return count
	return getNum

def numWords(user, text):
	return len(text.split())

def numChars(user, text):
	return len(text)

def readCsv(file, func=None):
	f = open(file, 'rb')
	reader = csv.reader(f)
	count = 0
	d = {}
	for row in reader:
		user = row[0]
		text = row[1]
		if user not in d:
			d[user] = []
		if func is None:
			d[user].append(1)
		else:
			data = func(user, text)
			d[user].append(data)
	return d

########## STAT FUNCTIONS ##########

def getNumFavorited(msg):
	num_favorited = msg['favorited_by']
	return len(num_favorited)

def getNumOfOccurances(word, once=True):
	def getNumOfMsgs(msg):
		text = msg['text']
		count = 0
		if text is None:
			return 0
		else:
			text = text.lower()
			if type(word) == list:
				for w in word:
					count += text.count(w)
			else:
				count = text.count(word)
			if once:
				return min(count, 1)
			else:
				return count
	return getNumOfMsgs

####################################

def getStats(data, ignoreGroupMe=True, total=True, percent=True, compact=True):
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
			if percent:
				l.append((str(k), num_msgs, total_data_per_person, 
					str(round(total_data_per_person * 100.0 / num_msgs, 1))+'%'))
			else:
				l.append((str(k), num_msgs, total_data_per_person))
		else:
			avg_data_len = 0
			if num_msgs != 0:
				avg_data_len = round(sum(v)*1.0 / num_msgs, 1)
			l.append((str(k), num_msgs, avg_data_len))
	l = sorted(l, key=lambda k:k[2], reverse=True)
#	if total:
#		l.append(('Average', round(total_msgs * 1.0 / num_people, 1), round(total_data * 1.0 / num_people, 1)))
#		l.append(('Total', total_msgs, total_data))
#	else:
#		l.append(('Average', round(total_msgs * 1.0 / num_people, 1), round(total_data * 1.0 / total_msgs, 1)))
#		l.append(('Total', total_msgs))
	if compact:
		return [(x[0],x[2]) for x in l]
	return l
	
##### GROUPME API Helper Functions ####
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
			user = msg['name']
			text = msg['text']
			if text is None:
				text == ""
			if user not in users:
				users[user] = []
			if csv_file:
				wr.writerow([user.encode('utf-8'), text.encode('utf-8')])
			if processTextFunc is not None:
				data = processTextFunc(msg)
				users[user].append(data)
		lastMsgId = msgs['messages'][-1]['id']
	return users

if __name__ == "__main__":
	## SAMPLE USAGE
	groups = getGroups()
	sorted_groups = sortByCount(groups)

	bball_id = groups['Bball']['id']
	traders_id = groups['Traders']['id']
	tx_id = groups['TXec \'13-\'14']['id']

	#bball_data = countMsgs(bball_id, csv_file='bball.csv')
	#traders_data = countMsgs(traders_id, csv_file='traders.csv')
	#tx_data = countMsgs(tx_id, csv_file='tx.csv')

	results = readCsv('bball.csv', getOccurances('lol', print_matches=True))
	print getStats(results)

