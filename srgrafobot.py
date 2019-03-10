import praw
from settings import *
from collections import defaultdict


reddit = praw.Reddit(user_agent=USER_AGENT,
                     client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     username=USERNAME,
                     password=PASSWORD)

print(reddit.read_only)

reddit.redditor('srgrafo').new()
i = 0
submission_ids = []
edit_storage = []

for submission in reddit.redditor('srgrafo').submissions.new():
    submission_ids.append(submission.id)

first_submission = reddit.submission(id=submission_ids[10])

# for top_level_comment in first_submission.comments:
#     print(top_level_comment.body)

print(first_submission.title)
first_submission.comments.replace_more(limit=None)

' Lets go down the reddit hole...' \
' This will parse down each tree down to five levels to see if any edit has been made'

# for top_level_comment in first_submission.comments:
#
#     for second_level_comment in top_level_comment.replies:
#
#         if second_level_comment.author.name == 'SrGrafo':
#             print('------------------------------------------------------------------')
#             print(top_level_comment.author.name + ": " + top_level_comment.body)
#             print(second_level_comment.author.name + ": " + second_level_comment.body + '\n')
#
#         for third_level_comment in second_level_comment.replies:
#
#             if third_level_comment.author.name == 'SrGrafo':
#                 print(second_level_comment.author.name + ": " + second_level_comment.body)
#                 print(third_level_comment.author.name + ": " + third_level_comment.body)
#
#             for fourth_level_comment in third_level_comment.replies:
#
#                 if fourth_level_comment.author.name == 'SrGrafo':
#                     print("Second")
#                     print(third_level_comment.author.name + ": " + third_level_comment.body)
#                     print(fourth_level_comment.author.name + ": " + fourth_level_comment.body)
#
#                 for fifth_level_comment in fourth_level_comment.replies:
#
#                     if fifth_level_comment.author.name == 'SrGrafo':
#                         print("Second")
#                         print(fourth_level_comment.author.name + ": " + fourth_level_comment.body)
#                         print(fifth_level_comment.author.name + ": " + fifth_level_comment.body)
#
# first_submission.comments.replace_more(limit=None)
# for comment in first_submission.comments.list():
#     if "EDIT" in comment.body:
#         if comment.author.name == "SrGrafo":
#
#             if not comment.is_root:
#                 ancestor = comment.parent()
#                 if not ancestor.author == None:
#
#                     print(ancestor.author.name + ": " + ancestor.body)
#                     print(comment.author.name + ": " + comment.body + '\n')
            #print(str(parent.author.score) + ": " + parent.body)
           # print(comment.body)

    #if hasattr(comment.author.name,'name') and comment.author.name == "SrGrafo":
       # print(comment.parent)
     #   print(comment.body)
   # print(comment.body)
   # print(first_submission.comments.list()

first_submission.comments.replace_more(limit=None)
edit_storage = [] #defaultdict(dict)

for comment in first_submission.comments.list():
    if not comment.is_root:
        ancestor = comment.parent()

        if not ancestor.author == None:
            if comment.author == "SrGrafo" and "EDIT" in comment.body:
               # edit_storage[comment.id] = {'author': ancestor.author.name,
                #                'comment': ancestor.body,
                 #               'edit': comment.body}

                tmp_list = [ancestor.author.name, ancestor.body, comment.author.name, comment.body, ancestor.permalink]
                edit_storage.append(tmp_list)
                   # print(ancestor.author.name + ": " + ancestor.body)
                   # print(comment.author.name + ": " + comment.body + '\n')

               # print(comment.author.name + ": " + comment.body + '\n')
              #  edit_storage.append(ancestor.author.name, ancestor.body, comment.author.name, comment.body)

print("|#|user|comment|EDIT|Link")
print("|:--|:--|:--|:--|:--|")
for i, entry in enumerate(edit_storage):
   # print(entry[0])
    print("|" + str(i) + "|" + entry[0] + "|" + entry[1] + "|" + entry[3] + "|[Link]("+ entry[4] + ")|")