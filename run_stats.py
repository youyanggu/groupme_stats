""" 
@author: youyanggu

Tool to show simple stats of GroupMe messages. It takes the csv file generated 
by retrieve_msgs.py as input.

"""

import csv
import argparse

parser = argparse.ArgumentParser(description='Tool to show simple stats of GroupMe messages.')
parser.add_argument('csv_file', help='CSV file to read messages from. Outputted by retrieve_msgs.py.')
# Arguments for getOccurances
parser.add_argument('-p', '--phrase', help='Find phrase(s)', nargs='+')
parser.add_argument('--print_matches', help='print all occurances of phrase', 
	action="store_true", default=False)
parser.add_argument('--count_dups', help='count multiple instances in same message', 
	action="store_true", default=False)
parser.add_argument('--match_exactly', help='the message must match the phrase exactly', 
	action="store_true", default=False)
parser.add_argument('--print_user', help='print all matches by this user')


# Arguments for showStats
parser.add_argument('--include_groupme', help='include messages sent by GroupMe', 
	action="store_true", default=False)
parser.add_argument('--average', help='take the average rather than the total', 
	action="store_true", default=False)
parser.add_argument('--no_compact', help='don\'t return the total num of messages and percentage', 
	action="store_true", default=False)

"""
Given a phrase, return a function that is passed to readCsv to count the number
of occurances of a certain phrase.

Params:
phrase - a single string or a list of strings to match for
count_dups - count multiple instances of a phrase in a message as a single instance
print_matches - print the messages that match the phrase
match_exactly - the message must match the phrase exactly
print_user - when print_matches is true, only print the matches by this user

"""
def getOccurances(phrase, count_dups=False, print_matches=False, match_exactly=False, print_user=None):
	def getNum(user, original_text):
		count = 0
		if original_text is None:
			return 0
		else:
			text = original_text.lower()
			if type(phrase) == list:
				for w in phrase:
					if match_exactly:
						if text == w: count = 1
					else:
						count += text.count(w)
			else:
				if match_exactly:
					if phrase == text: count = 1
				else:
					count = text.count(phrase)
			if count > 0 and (print_matches or print_user == user):
				print user, ':', original_text
			if count_dups:
				return min(count, 1)
			else:
				return count
	return getNum

def numWords(user, text):
	return len(text.split())

def numChars(user, text):
	return len(text)

""" Reads the CSV file and passes the content to process_msg_func """
def readCsv(fname, process_msg_func=None):
	f = open(fname, 'rU')
	reader = csv.reader(f)
	count = 0
	d = {}
	for row in reader:
		if len(row) < 3:
			raise IOError("CSV file missing columns.")
		group_name = row[0]
		timestamp = row[1]
		user = row[2]
		text = row[3]
		if user not in d:
			d[user] = []
		if process_msg_func is None:
			d[user].append(1)
		else:
			data = process_msg_func(user, text)
			d[user].append(data)
	return d

""" Helper function that calls readCsv and getStats """
def showStats(fname, func=None, **kwargs):
	result = readCsv(fname, func)
	return getStats(result, **kwargs)

""" 
Given the return value of readCsv, display useful stats 

Params:
data - dictionary where the key is the user's name and the value is a list that contains an
		integer for each message by the user (typically representing the # of phrases matched)
include_groupme - include messages sent by GroupMe
total - sum the list of integers rather than take the average. If we're counting phrase 
		occurances, then total=True. If we are counting avg message length, then total=False
percent - display the number of matches as a percentage of total messages
compact - don't return the total num of messages and percentage
"""
def getStats(data, include_groupme=False, total=True, percent=True, compact=True):
	l = []
	num_people = total_msgs = total_data_per_person = total_data = 0
	for k,v in data.iteritems():
		if not include_groupme and str(k) == 'GroupMe':
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


if __name__ == "__main__":
	args = parser.parse_args()
	csv_file = args.csv_file
	if args.phrase:
		result = readCsv(csv_file, getOccurances(
								  args.phrase, 
								  print_matches=args.print_matches,
								  count_dups=args.count_dups,
								  match_exactly=args.match_exactly,
								  print_user=args.print_user)
						)
		print getStats(result,
					   include_groupme=args.include_groupme,
					   total=(not args.average), 
					   compact=(not args.no_compact)
					  )
	else:
		print showStats(csv_file,
						None,
						include_groupme=args.include_groupme,
					   	total=(not args.average), 
					   	compact=(not args.no_compact)
					   	)
	
