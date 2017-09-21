import random
import urllib
import re
import io
import requests
import json
import traceback
import time
import ConfigParser, os
import twitter as TwitterAPI

try:
    f = open('config.cfg');
    config = ConfigParser.ConfigParser()
    config.readfp(f)
    twitter = config._sections["Twitter"]
    danbooru = config._sections["danbooru"]
except:
    print("Invalid config")

api = TwitterAPI.Api(consumer_key=twitter['consumer_key'],
                  consumer_secret=twitter['consumer_secret'],
                  access_token_key=twitter['access_token_key'],
                  access_token_secret=twitter['access_token_secret'])

def trim(user, name, imgL):
    fin = ""
    count = 0
    while True:
        if len(fin) == (90 - len(user)) or fin == name:
            break
        fin = fin + name[count]
        count = count+1
    return "@"+user+fin+" "+imgL

def series(word):
    if word == '-k':
        return 'kancolle'
    elif word == '-i':
        return 'idolmaster'
    elif word == '-t':
        return 'touhou'
    elif word == '-g':
        return 'gochiusa'
    else:
        return None


def choose_opt(choices, status):
    if len(choices) < 2:
        print(time.strftime("[%x %X] ")+"Error: No choices given")
        return
    del choices[0]
    if len(choices) != 0:
        made= [x.strip() for x in choices[0].split(',')]
        print(time.strftime("[%x %X] ")+"Choices: "+str(made))
        for item in made[:]:
            if '@' in item:
                if ' ' not in item:
                    made.remove(item)
        choices = made
        length = len(choices)
        if(length < 1):
            return
        choice = choices[random.randint(0, length-1)]
        print(time.strftime("[%x %X] ")+"Reply: "+str(choice))
        fin_status = "@"+str(status['user']['screen_name'])+" I suggest you "+choice
        r = api.PostUpdate(fin_status[:140], in_reply_to_status_id = status['id_str'])
        print(time.strftime("[%x %X] ")+"Successfully tweeted reply!")

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

        arg = re.compile(r'-[a-z] ')
        if arg.search(made[0].lower()):
            ans = series(made[0][0:2])
            if ans != None:
                made[0] = made[0][3:]
                made.insert(0,ans)

        print(time.strftime("[%x %X] ")+"Tags: "+str(made))
        randURL = 'https://danbooru.donmai.us/posts/random?tags='
        count = 1
        for dec in made:
            if count == 4:
                break
            randURL += urllib.quote(dec.replace(" ","_"))+"+"
    else:
        randURL = 'https://danbooru.donmai.us/posts/random?tags='
    count = 20
    max_post = [None,-1,0]
    while True:
        if count == 0:
            raise
        payload = {'login': danbooru['login'], 'api_key': danbooru['api_key']}
        response = requests.get(randURL, params=payload)
        src =re.search('(?<=posts/).*\?',response.url).group(0).replace("?","")
        url = 'https://danbooru.donmai.us/posts/'+src+".json"
        r = requests.get(url, params=payload).json()
        if r['rating'] != "s":
            print(time.strftime("[%x %X] ")+"NSFW: "+src)
            count = count - 1
            continue
        elif int(r['score'])<7:
            print(time.strftime("[%x %X] ")+"Score of "+str(r['score'])+" : "+src)
            if r['score'] > max_post[1]:
                max_post[0] = r
                max_post[1] = r['score']
                max_post[2] = src
            count = count - 1
            if count == 0:
                r = max_post[0]
                src = max_post[2]
                print(time.strftime("[%x %X] ")+"SFW: "+max_post[2])
                break
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
    try:
        file = requests.get(img)
        data = file.content
        fin_status = trim(str(status['user']['screen_name']),name,imgL)
        r = api.PostMedia(fin_status, in_reply_to_status_id = status['id_str'], media=io.BytesIO(data))
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise
    print(time.strftime("[%x %X] ")+"Successfully tweeted reply!")

while True:
    print(time.strftime("[%x %X] ")+"Starting twitter bot...")
    names = {}
    try:
        r = api.GetStreamFilter(follow=[twitter['handle']])
        for status in r:
            if 'text' in status and str(status['user']['id']) != twitter['handle']:
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
                    r = api.PostUpdate("@"+str(status['user']['screen_name'])+" No pictures found." , in_reply_to_status_id = status['id_str'])
            elif 'disconnect' in status:
                event = status['disconnect']
                if event['code'] in [2,5,6,7]:
                    # something needs to be fixed before re-connecting
                    raise Exception(event['reason'])
                else:
                    # temporary interruption, re-try request
                    break
    except Exception as e:
        print(e)
        raise
    except:
        # temporary interruption, re-try request
        pass
