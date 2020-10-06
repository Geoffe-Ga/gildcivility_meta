import json
import pymongo
from pprint import pprint
from pathlib import Path
import sys
import getopt
import datetime
import os
from gildcivility_helpers import RedditCrawler as r


arg_help = """
-i: Input File:
    *.txt file with utf-8 encoding. 

-c: Commands:
    length              Rejection poem for triggers with too few characters 
    score               Rejection poem for triggers with too few upvotes
    no_parent           Rejection poem for triggers with no available flag
    good                Solicitation poem for triggers that meet all criteria
    header              Initial Bot post header
    footer              Initial Bot post footer
    subreddits          Subreddits that the bot can post in
    bot_reddit_id       Bot's unique id
    min_ages            Minimum ages for all active subreddits
    get_min_ages        Queries Reddit to get min ages for all active subreddits
"""


def update(cmd, inp):
    print("Uploading input to mongo:")
    pprint(inp)
    db = connect()
    if db.post.count_documents({"type": cmd, "active": True}):
        for document in db.post.find({"type": cmd, "active": True}):
            _id = document["_id"]
            db.post.update_one({"_id": _id}, {"$set": {"active": False}})

    try:
        inp = json.loads(inp)
    except ValueError:
        pass

    payload = dict()
    payload["body"] = inp
    payload["active"] = True
    payload["type"] = cmd
    payload["created_at"] = datetime.datetime.utcnow().isoformat(sep=' ')
    payload["updated_at"] = datetime.datetime.utcnow().isoformat(sep=' ')
    print("Full Mongo Dump:")
    pprint(payload)
    db.post.insert_one(payload)


def get_min_ages():
    db = connect()
    subreddits = db.post.find_one({"type": "subreddits", "active": True})
    reddit = r.reddit
    res = {}
    for subreddit in subreddits["body"]:
        res[subreddit] = 48
        for submission in reddit.subreddit(subreddit).top(time_filter="day"):
            for comment in submission.comments:
                if comment.score > 1:
                    age = datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(comment.created_utc)
                    age = age.seconds / 60 // 60
                    if age < res[subreddit]:
                        res[subreddit] = age
            break
    return res


def connect():
    mongo_auth = os.environ.get("MONGO")
    db = pymongo.MongoClient(mongo_auth).civility
    print("Successfully connected. Found Collections:", db.list_collection_names())
    return db


def main(argv):
    file_path = None
    cmd = None
    try:
        try:
            opts, args = getopt.getopt(argv, "i:c:", ["input=", "cmd="])
            print(opts, args)
        except getopt.GetoptError as err:
            print(err)
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-i", "--input"):
                file_path = str(Path.cwd()) + "/" + arg
            elif opt in ("-c", "--cmd"):
                cmd = arg
        if not (file_path or not cmd) and cmd != "get_min_ages":
            print("meta_update.py -i <inputfile> -c <command>")
            print(arg_help)
            sys.exit(2)
        if file_path:
            file = open(file_path, 'r').read()
    except FileNotFoundError:
        if cmd != "get_min_ages":
            print("File Not Found. ({})".format(file_path))
            print("\nMake sure it is in your PWD, check spelling and try again. \nExiting.")
            sys.exit()

    if cmd == "get_min_ages":
        min_ages = get_min_ages()
        if not min_ages:
            print("No Active Subreddits")
        else:
            pprint(min_ages)
    else:
        update(cmd=cmd, inp=file)
        print("success!")


if __name__ == '__main__':  main(sys.argv[1:])

