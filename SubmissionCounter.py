# SubmissionCounter.py

import praw
import time
import calendar
import inspect
import sys
import pickle
import Secrets # Separate file in the same directory, with passwords, API keys, etc.

MAX_SUBMISSIONS_PULL = 800 # How many submissions should it attempt to process before stopping?

# function for debugging purposes
def tellMeEverything(x):	
	for member in inspect.getmembers(x):
		print(member)
	return

# function to return the Unix epoch time of the beginning of the most recent week
def whenWasLastMonday():
	now = time.gmtime();
	while (now[6] != 0):
		now = time.gmtime(calendar.timegm(now) - 86400)
	rewritableTime = list(now)
	rewritableTime[3] = 0
	rewritableTime[4] = 0
	rewritableTime[5] = 0
	now = time.struct_time(tuple(rewritableTime))
	return calendar.timegm(now)

reddit = praw.Reddit(client_id=Secrets.CLIENT_ID, client_secret=Secrets.CLIENT_SECRET, username=Secrets.REDDIT_USERNAME, password=Secrets.REDDIT_PASSWORD, user_agent='/r/Catholicism helper bot')

subreddit = reddit.subreddit('catholicism')
#tellMeEverything(subreddit)

newsubmissions = subreddit.new(limit=None)
#tellMeEverything(newsubmissions)

PREFERRED_SAVE_FILE_NAME = "submissionsListSerialized.data"  # Whatever you want to call the filename where it saves the dict submissions

try:
	fileObject = open(PREFERRED_SAVE_FILE_NAME,'rb')  
	submissions = pickle.load(fileObject)
	fileObject.close()
except Exception as e:
	submissions = {}
	print("Failed to load from ", PREFERRED_SAVE_FILE_NAME, "; ", e)

lastMonday = whenWasLastMonday()
totalSubmissionsProcessed = 0
submissionsAlreadySeen = 0
submissionsBeforeMonday = 0
while totalSubmissionsProcessed < MAX_SUBMISSIONS_PULL:
	try:
		submission = next(newsubmissions)
	except StopIteration:
		break  # Nothing more to get; stop the loop
	except Exception as e:
		print ("Something else went wrong: ", e)
		break  # Something else went wrong; stop the loop
	if submission.created_utc > lastMonday:
		if hasattr(submission, "author") and hasattr(submission.author, "name"):  # Deleted posts/accounts can cause problems
			author = str(submission.author.name)
			if author not in submissions.keys():
				submissions[author] = {}
			submissionID = str(submission.id)
			if submissionID in submissions[author].keys():
				submissionsAlreadySeen += 1
			else:
				submissions[author][submissionID] = {"title": str(submission.title), "time": round(float(submission.created_utc)), "is_self": submission.is_self, "url": submission.url}
		#else:	
			#tellMeEverything(submission)
	else:
		submissionsBeforeMonday += 1
	totalSubmissionsProcessed += 1

# Sort submitters by username, then for all with three or more posts, print out the total count and the dates of the posts.
for key in sorted(submissions.items()):
	author = key[0]
	if len(submissions[author]) >= 4:
		datesstring = ""
		for id in submissions[author]:
			if submissions[author][id]["is_self"]:
				datesstring += "Self-Post: " + submissions[author][id]["title"][0:30] 
			else:
				datesstring += "Link to: " + submissions[author][id]["url"][0:30]
			datesstring += time.strftime(" at %a %b %d ", time.gmtime(submissions[author][id]["time"])) + "\n"
		print(author, ":", len(submissions[author]))
		print(datesstring)

print("Complete - reviewed ", totalSubmissionsProcessed, " posts")
print(submissionsAlreadySeen, " were from this week, but already seen")
print(submissionsBeforeMonday, " were from last week")

try:
	fileObject = open(PREFERRED_SAVE_FILE_NAME,'wb') 
	try:
		pickle.dump(submissions,fileObject)   
	except PicklingError:
		print ("Submissions can't be pickled; ", e)
	except Exception as e:
		print ("Something else went wrong: ", e)
	fileObject.close()
except Exception as e:
	print("Failed to open ", PREFERRED_SAVE_FILE_NAME, ";", e)

#input('Press ENTER to exit')  # If you are running this code in an environment where it exits the window as soon as execution is complete, uncomment this line.