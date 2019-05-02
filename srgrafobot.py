import praw
from peewee import *

from secret import *
from settings import *
from srgrafobot_peewee import User, Submission
from datetime import datetime
from praw.exceptions import APIException

import hashlib
import logging

import time

# Log everything
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler("{0}/{1}.log".format("./logs/", "srgrafobot")),
        logging.StreamHandler()
    ])

logger = logging.getLogger()

# What is currently missing:
# The bot needs to detect a new post, and start his collection post. Then he has to keep monitoring this thread and
# whenever an update is posted, update the original post with his edit

# Setting up the PRAW user
reddit = praw.Reddit(user_agent=USER_AGENT,
                     client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     username=USERNAME,
                     password=PASSWORD)

db = SqliteDatabase(DB)

def check_for_submissions():
    logger.info("Starting script")

    'Check if SrGrafo has published a new post. If he did not, do nothing, if he did, trigger new routine.'

    'Check for current submissions that are still going'
    list_curr = check_for_current_submissions()

    list_new = check_for_new_submissions()

    if OVERRIDE_SUBMISSIONS:
        list_total = OVERRIDE_LIST

        logger.warning("There are %s entries but OVERRIDE_SUBMISSIONS is overwriting this.", len(OVERRIDE_LIST))



    else:
        list_total = list_curr + list_new

    'If there is a new entry, start routine'
    for entry in list_total:
        logger.info("---------------------")
        logger.info("Starting the process now for ID %s", entry)
        make_entry(entry)

    if RUN_TIMED:
        wait(WAITTIME)


def check_for_current_submissions():
    'Check if a post is still current within defined timelimit'

    current_sub = Submission.select().where(Submission.thread == True)
    list_ids = []

    for submission in current_sub:

        if time_difference_to_now(submission.date) < HOUR_THRESHOLD:
            list_ids.append(submission.thread_id)

    logger.info("Found %s IDs in current submissions", len(list_ids))
    logger.debug("In current submission there are the following IDs: %s", list_ids)

    return list_ids


def check_for_new_submissions():
    'Check if SrGrafo has published a new post. If he did not, do nothing, if he did, trigger new routine.'

    'Get all DB entries from SrGrafo'
    db.connect()
    list_ids = []
    grafo_submissions = Submission.select().where(User.username == "/u/SrGrafo", Submission.thread is True)

    'Get all submission IDs from SrGrafo'
    # Go through all of SrGrafos submissions and add them to a list
    for submission in reddit.redditor('srgrafo').submissions.new():
        #submission_ids.append(submission.id)

        user = User.get(User.username == '/u/SrGrafo')

        submission_new, created = Submission.get_or_create(
            thread_id=submission.id,
            defaults={
                'user':user,
                'date':submission.created_utc,
                'title':submission.title,
                'thread':True,
                'comment':False,
                'post_created':False
                }
        )

        if created:
            list_ids.append(submission_new.thread_id)

    db.close()
    logger.info("Found %s new entries", len(list_ids))
    logger.debug("Found the following new entries: %s", list_ids)
    return(list_ids)


def make_entry(thread_id):
    'Check for existing table'

    # Pick an ID from the list (only for development
    submission = reddit.submission(id=thread_id)

    submission.comments.replace_more(limit=None)

    check_existing = check_for_existing_table(submission)

    if check_existing is not False:
        logger.info("This entry already does have a table to maintain")
        update_table(check_existing, submission)

    else:
        logger.info("This thread is without table, let's create it")
        create_new_table(submission)


def check_for_existing_table(submission):
    'Check if the bot has already posted a message, if so, just make sure to update it'

    # Expand the "read more" for the full thread

    # Loop through all comments
    for comment in submission.comments.list():
        logger.debug("Check comment author: %s", comment.author)

        # Make sure the comment is not on root level before ancestor is pinged
        if comment.is_root:

            # Identify SrGrafo edit: His username and "EDIT" in the comment field
            if comment.author == "srgrafo_edit_bot":
                summary_comment_id = comment.id
                logger.info("Existing post detected in thread with comment ID %s", summary_comment_id)
                return summary_comment_id

            else:
                response = False

    logger.info("No existing comment was found")
    return response


def create_new_table(submission):
    'Create a new table if the other one is not present'

    body = create_full_post_content(submission)

    if body is not False:

        if WRITE_REPLIES:
            try:
                submission.reply(body)
                logger.info("A new post in thread %s (ID: %s) was made", submission.title, submission.id)
                logger.debug("A new post in thread %s (ID: %s) was made with the following content \n %s", submission.title, submission.id, body)

                db.connect()
                new_db_entry = Submission.get(Submission.thread_id == submission.id)
                new_db_entry.post_created = True
                new_db_entry.save()
                db.close()

            except APIException as error:
                logger.error(error)
                pass


        else:
            logger.info("Would have posted in this thread, but SETTINGS prohibited it.")



def get_grafo_edits(submission):
    'Gets all grafo edits and creates hashes to compare them'

    ' Lets go down the reddit hole...' \
    ' This will parse down each tree down to five levels to see if any edit has been made'

    # Expand the "read more" for the full thread
    submission.comments.replace_more(limit=None)

    # Setup the empty dict
    edit_storage = []

    # Loop through all comments
    for comment in submission.comments.list():

        # Make sure the comment is not on root level before ancestor is pinged
        if not comment.is_root:
            ancestor = comment.parent()

            # Make sure ancestor is not a deleted comment which throws an error message
            if not ancestor.author is None:

                # Identify SrGrafo edit: His username and "EDIT" in the comment field
                if comment.author == "SrGrafo" and "EDIT" in comment.body:

                    # Get rid of line breaks
                    ancestor_body = ancestor.body.replace('\n', ' ').replace('\r', '')
                    comment_body = comment.body.replace('\n', ' ').replace('\r', '')

                    # Put everything in a temporary list
                    tmp_list = [ancestor.author.name, ancestor_body, comment.author.name, comment_body, ancestor.permalink]

                    hash_string = ""
                    for entry in tmp_list:
                        hash_string += str(entry)

                    hash = hashlib.md5(hash_string.encode('utf-8')).hexdigest()
                    tmp_list.append(hash)

                    # Append temp list to longer list
                    edit_storage.append(tmp_list)

    return edit_storage


def create_full_post_content(submission):

    post_content = get_grafo_edits(submission)

    if len(post_content) > 0:

        'Let me post this'
        # Give back current result that could be copy pasted into module
        body = ""
        body += "###" + submission.title + "\n" \
                + "|#|user|comment|EDIT|Link" + "\n" \
                + "|:--|:--|:--|:--|:--|" + "\n"

        for i, entry in enumerate(post_content):

            if entry[0] == 'srgrafo_edit_bot':
                entry[1] = '[HA! YOU ALMOST GOT ME TO CREATE A BLACK HOLE, FELLOW HUMAN! BUT AS GOOD HUMAN, I SAW THROUGH YOUR EFFORTS, HAHA]'

            body += "|" + str(i) + "|/u/" + entry[0] + "|" + entry[1] + "|" + entry[3] + "|[Link](" + entry[4] + ")|" + "\n"

        body += "\n \n" + "I am a little fan-made bot who loves /u/SrGrafo but is a little lazy with hunting for EDITs. If you want to support our great creator, check out his [Patreon](https://Patreon.com/SrGrafo)"

        return body

    else:
        logger.info("No EDITs found, process aborted.")
        return False

def update_table(check_existing, submission):

    'Find my own post'

    db.connect()
    new_db_entry = Submission.get(Submission.thread_id == submission.id)
    new_db_entry.post_created = True
    new_db_entry.save()
    db.close()

    'For each row in table, start hashing'
    logger.info("Existing post in %s is being updated", check_existing)
    comment = reddit.comment(check_existing)

    post_content = create_full_post_content(submission)

    comment_hash = hashlib.md5(comment.body.encode('utf-8')).hexdigest()
    post_content_hash = hashlib.md5(post_content.encode('utf-8')).hexdigest()

    post_comparison = (comment_hash == post_content_hash)

    if post_content is not False and post_comparison is False:
        if WRITE_REPLIES:
            comment.edit(post_content)
            logger.info("Post %s was updated", check_existing)

        else:
            logger.info("Would have updated this table, but SETTINGS prohibited it.")

    else:
        logger.info("No need to update post.")


def time_difference_to_now(time1):

    now = datetime.utcnow()

    time1 = datetime.utcfromtimestamp(time1)
    diff = (now - time1).total_seconds() / 3600

    return diff

def wait(wait_time):
    logger.info("Let's wait for %s", WAITTIME)
    time.sleep(wait_time)
    check_for_submissions()

check_for_submissions()
