import random
import urllib
import re
import requests
import json
import time
import ConfigParser, os
from TwitterAPI import TwitterAPI
from TwitterAPI.TwitterError import *

try:
    f = open('keys.cfg');
    config = ConfigParser.ConfigParser()
    config.readfp(f)
    twitter = config._sections["Twitter"]
    danbooru = config._sections["danbooru"]
except:
    print("Invalid config")

api = TwitterAPI(twitter['consumer_key'], twitter['consumer_secret'], twitter['access_token_key'], twitter['access_token_secret'])

def choose_opt(choices, status):
    del choices[0]
    if len(choices) != 0:
        made = [x.strip() for x in choices[0].split(',')]
        print(time.strftime("[%x %X] ")+"Choices: "+str(made))
        choices = made
        length = len(choices)
        choice = choices[random.randint(0, length-1)]
        print(time.strftime("[%x %X] ")+"Reply: "+str(choice))
        r = api.request('statuses/update', {'status':"@"+str(status['user']['screen_name'])+" I suggest you "+choice, 'in_reply_to_status_id': status['id_str']})

def pic_opt(choices, status, names):
    reroll = False
    if choices[0].lower() == "!reroll":
        reroll = True
        try:
            choices = names[status['user']['screen_name']][0]
        except:
            raise
    else:
        names[status['user']['screen_name']] =  [choices, "0"]
        del choices[0]
    if len(choices) != 0:
        made = [x.strip() for x in choices[0].split(',')]
        print(time.strftime("[%x %X] ")+"Tags: "+str(made))
        randURL = 'https://danbooru.donmai.us/posts/random?tags=idolmaster'
        count = 1
        for dec in made:
            if count == 4:
                break
            randURL += "+"+dec.replace(" ","_")
    else:
        randURL = 'https://danbooru.donmai.us/posts/random?tags=idolmaster'
    count = 20
    while True:
        if count == 0:
            raise
        payload = {'login': danbooru['login'], 'api_key': danbooru['api_key']}
        response = requests.get(randURL, params=payload)
        src =re.search('(?<=posts/).*\?',response.url).group(0).replace("?","")
        url = 'https://danbooru.donmai.us/posts/'+src+".json"
        r = requests.get(url, params=payload).json()
        if r['rating'] != "s" or int(r['score'])<7 :
            print(time.strftime("[%x %X] ")+"NSFW: "+src)
            count = count - 1
            continue
        else:
            if reroll == False:
                names[status['user']['screen_name']][1] = src
            else:
                if src == names[status['user']['screen_name']][1]:
                    print(time.strftime("[%x %X] ")+"Duplicate picture... rerolling")
                    continue
            print(time.strftime("[%x %X] ")+"SFW: "+src)
            break
    img = "https://danbooru.donmai.us"+r['file_url']
    name = " "+r['tag_string_character'].replace(" ",", ").replace("_", " ")
    imgL = "https://danbooru.donmai.us/posts/"+src
    file = urllib.urlopen(img)
    data = file.read()
    r = api.request('media/upload', None, {'media': data})
    if r.status_code == 200:
        media_id = r.json()['media_id']
        r = api.request(
            'statuses/update', {'status':"@"+str(status['user']['screen_name'])+name+" "+imgL, 'media_ids': media_id, 'in_reply_to_status_id':status['id_str']})
    else:
        print(time.strftime("[%x %X] ")+"An error occured while uploading media...")

while True:
    print(time.strftime("[%x %X] ")+"Starting twitter bot...")
    names = {}
    try:
        r = api.request('statuses/filter', {'track': '@minerhost'})
        for status in r:
            if 'text' in status:
                print(time.strftime("[%x %X] ")+"New request from: "+status['user']['screen_name'])
                choices = status['text'].encode('utf-8').split(' ',2)
                del choices[0]
                try:
                    if choices[0].lower() == "!choose":
                        choose_opt(choices, status)
                except:
                    print(time.strftime("[%x %X] ")+"Invalid request: "+status['text'].encode('utf-8'))
                    continue
                try:
                    if choices[0].lower() == "!pic" or choices[0].lower() == "!reroll":
                        pic_opt(choices, status, names)
                except:
                    print(time.strftime("[%x %X] ")+"An error occured or there are no pictures found...")
                    r = api.request('statuses/update', {'status':"@"+str(status['user']['screen_name'])+" No pictures found.", 'in_reply_to_status_id':status['id_str']})
            elif 'disconnect' in status:
                event = status['disconnect']
                if event['code'] in [2,5,6,7]:
                    # something needs to be fixed before re-connecting
                    raise Exception(event['reason'])
                else:
                    # temporary interruption, re-try request
                    break
    except TwitterRequestError as e:
        if e.status_code < 500:
            # something needs to be fixed before re-connecting
            raise
        else:
            # temporary interruption, re-try request
            pass
    except TwitterConnectionError:
        # temporary interruption, re-try request
        pass
