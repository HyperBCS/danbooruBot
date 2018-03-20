import praw
import random
import time
import requests
import re
import datetime
import ConfigParser, os, io
import json
import twitter as TwitterAPI
import urllib

try:
    f = open('/root/twitter/reddit/keys.cfg');
    config = ConfigParser.ConfigParser()
    config.readfp(f)
    reddit = config._sections["reddit"]
    twitter = config._sections["Twitter"]
    danbooru = config._sections["danbooru"]
except:
    print("Invalid config")

api = TwitterAPI.Api(consumer_key=twitter['consumer_key'],
                  consumer_secret=twitter['consumer_secret'],
                  access_token_key=twitter['access_token_key'],
                  access_token_secret=twitter['access_token_secret'])


user_agent = "anime pic 1.0 by /u/hyperbcs"
r = praw.Reddit(client_id=reddit['client_id'], client_secret=reddit['client_secret'],user_agent=user_agent)
count = 0

def un_reddit(title):
    pattern = [re.compile("\(.*x-post.*\)", re.IGNORECASE),re.compile("\[.*x-post.*\]", re.IGNORECASE),re.compile("\(.*comment.*\)", re.IGNORECASE),re.compile("\[.*comment.*\]", re.IGNORECASE),
    re.compile("\(.*xpost.*\)", re.IGNORECASE),re.compile("\[.*xpost.*\]", re.IGNORECASE),re.compile(" x-post.*", re.IGNORECASE),re.compile(" x-post.*", re.IGNORECASE),
    re.compile(" xpost.*", re.IGNORECASE),re.compile(" xpost.*", re.IGNORECASE)]
    for pt in pattern:
        title = pt.sub('',title)
    return title

def upload(data, title):
    try:
        data = file.content
        req = api.PostMedia(un_reddit(title)[:117], media=io.BytesIO(data))
        print(time.strftime("[%x %X] ")+"Successfully tweeted picture!")
    except Exception as e:
        print(e)
        print(time.strftime("[%x %X] ")+"An error occured while uploading media with status code "+str(req.status_code))
        raise

while count < 10:
    count = count + 1
    try:
        timeS = random.randint(1357084800, int(time.time())-86400)
        query = "(and timestamp:"+str(timeS)+".."+str(timeS+86400)+")"
        search = r.subreddit('awwnime').search(query, sort='new',syntax='cloudsearch', limit=100)
        count2 = 0
        while count2 < 20:
            count2 =count2 + 1
            post = next(search)
            rem = re.compile(r'.*removed.png')
            if post.score < 100:
                print(str(post.score)+" Score too low... retrying")
                continue
            elif post.is_self != False:
                print("Not a self post")
            file = requests.get(post.url)
            if rem.search(file.url):
                print(time.strftime("[%x %X] ")+"Image removed... retrying")
                continue
            print(time.strftime("[%x %X] ")+"["+str(post.score)+"]"+" "+un_reddit(post.title.encode('utf-8')))
            print(time.strftime("[%x %X] ")+datetime.datetime.fromtimestamp(post.created).strftime("%m-%d-%Y %H:%M:%S"))
            print(time.strftime("[%x %X] ")+file.url)
            upload(file, post.title.encode('utf-8'))
            break
        break
    except StopIteration:
        print("No pictures... trying again")
    except Exception as e:
    	print(e)
        print("An error occured... retrying")
        time.sleep(1)