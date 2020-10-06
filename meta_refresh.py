import io
import os
from pymongo import MongoClient
from pathlib import Path
import json

mongo_auth = os.environ.get("MONGO")
mongo = MongoClient(mongo_auth)
[print(name) for name in mongo.civility.list_collection_names()]
print("Initialized.")


def get_tools():
        tools = list()
        for tool in mongo.civility.post.find(tools_query):
            tools.append([tool["type"], tool["body"]])
        for post in mongo.civility.post.find(posts_query):
            tools.append([post["type"], post["body"]])
        return tools


posts_query = {"type": {"$in": ["length", "score", "no_parent", "good", "header", "footer"]}, "active": True}
tools_query = {"type": {"$in": ["subreddits", "min_ages", "bot_reddit_uid"]}, "active": True}

tools = get_tools()

print("Found tools")
[print(tool[0], "\n", tool[1], "\n") for tool in tools]

for tool in tools:
    with io.open(str(Path.cwd()) + "/" + tool[0] + ".txt", "w", encoding="utf8") as fo:
        if isinstance(tool[1], dict) or isinstance(tool[1], list):
            tool[1] = json.dumps(tool[1])
        fo.write(tool[1])
        print("Wrote", tool[0]+".txt")
