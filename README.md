Download GroupMe Messages
=============

This is a tool to download GroupMe messages to a CSV file and display simple stats about those messages.

Example usage:
- Number of messages by each user
- Number of favorited messages
- Number of times a user spews profanity
- Average length of a user's message
- Number of times a user says "lol"

Getting Access Token
--------------
In order to download GroupMe messages, you need an unique access token provided to you by GroupMe. To get this, log into GroupMe's <a href="https://dev.groupme.com" target="_blank">Developers</a> website and click Access Token. You should then be given a 40 character long access token.

Dependencies
--------------
You might need to install Python's <a href="http://docs.python-requests.org/en/latest/" target="_blank">request</a> library: ```pip install requests```

Instructions
--------------
1. Get your GroupMe Access Token using the instructions above.
2. Run ```python retrieve_msgs.py```, pass in your access token, and follow the command line interface to download your GroupMe messages to a CSV file. Use ```python retrieve_msgs.py --help``` to see a list of commands.
  - For example: ```python retrieve_msgs.py <YOUR ACCESS TOKEN> -a -c output.csv``` will output all of your messages into a csv file called output.csv.
3. Run ```python run_stats.py``` and pass in your CSV file to display some simple stats about your messages. Use ```python run_stats.py --help``` to see a list of commands. For example: ```python run_stats.py output.csv``` will simply give you the number of messages sent by each individual.
