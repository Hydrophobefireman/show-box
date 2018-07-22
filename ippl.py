import json
import random
import re
from time import sleep
from urllib.parse import urlparse as urlp_, urlencode

import requests
from bs4 import BeautifulSoup as bs

import dbmanage
import upload


def get_(url, v=True, n=1, season=0):
    ua = random.choice(["Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US) AppleWebKit/604.1.38 (KHTML, like Gecko) Chrome/68.0.3325.162",
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0_2 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A421 Safari/604.1",
                        "Mozilla/5.0 (Linux; Android 8.1.0; Pixel Build/OPM1.171019.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.137 Mobile Safari/537.36",
                        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
                        ])
    print("[debug]Fetching:\n", url)
    basic_headers = {
        "User-Agent": ua,
        "Upgrade-Insecure-Requests": "1",
        "dnt": '1',
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
    }
    sess = requests.Session()
    to_screen(["[debug]Using Standard Headers:"], v)
    dict_print(basic_headers, v=v)
    page = sess.get(url, headers=basic_headers, allow_redirects=True)
    to_screen(["[debug]Page URL:", page.url], v)
    to_screen(["[debug]Cookie Jar For %s:" %
               (page.url)], v)
    dict_print(dict(page.cookies), v)
    soup = bs(page.text, "html.parser")
    to_screen(["\n[debug]Finding Title"], v)
    title = soup.find(
        "input", attrs={"name": "movies_title"}).attrs["value"]
    to_screen(["[debug]Found:", title], v)
    to_screen(["[debug]Finding Thumbnail"], v)
    thumbnail = soup.find(
        "input", attrs={"name": "phimimg"}).attrs["value"]
    to_screen(["[debug]Found", thumbnail], v)
    if thumbnail.startswith("/"):
        if thumbnail.startswith("//"):
            thumbnail = "https:"+thumbnail
        else:
            thumbnail = input("fix the thumbnail:")
    to_screen(["[debug]Fetching Thumbnail and uploading to cdn"], v)
    image = upload.upload(thumbnail).get("secure_url")
    to_screen(["[debug]Secure URL of Image:", image], v)
    url_ = page.url
    to_screen(["[debug]Adding Referer to headers"], v)
    basic_headers = {**basic_headers, "Referer": url_}
    to_screen(["[debug]Adding X-Requested-With to headers"], v)
    basic_headers = {**basic_headers, "X-Requested-With": "XMLHttpRequest"}
    parsed_url = urlp_(url_)
    host = "https://"+parsed_url.netloc+"/"
    div = soup.find(attrs={"id": "list-eps"})
    to_screen(["[debug]Finding Ipplayer Configs"], v)
    if div is None:
        raise Exception("Could Not Find Ipplayer Configs")
    tags = div.findChildren(attrs={"data-next": True})
    number_of_eps = len(tags)
    episode_data = {}
    for i in range(n, number_of_eps+1):
        attrs_ = tags[i-1]
        to_screen(['[debug]Fetching Config URLs for episode number:', i], v)
        data_headers = {"keyurl": '%d' % (
            i), "postid": "server", "phimid": attrs_.attrs['data-film']}
        to_screen(['\n[debug]Sending Config:'], v)
        dict_print(data_headers, v)
        toparse = sess.post(host+"index.php", data=data_headers,
                            cookies=page.cookies)
        parsed_data = bs(toparse.text, 'html.parser')
        tgs = parsed_data.find_all("a")
        data = []
        for t in tgs:
            to_send = t.attrs
            to_screen(["[debug]Working with the configs of", t.string], v)
            to_screen(["[debug]Found Configs:"], v)
            dict_print(t.attrs, v)
            to_screen(["[debug]Sleeping for 2 seconds"], v)
            sleep(1)
            a = sess.post(host+"ip.file/swf/plugins/ipplugins.php", headers=basic_headers, data={
                "ipplugins": 1, "ip_film": to_send["data-film"], "ip_server": to_send["data-server"], "ip_name": to_send["data-name"], "fix": 'null'})
            b = json.loads(a.text)
            sleep(1)
            to_screen(["[debug]Recieved:"], v)
            dict_print(b, v)
            ret = sess.post(host+"ip.file/swf/ipplayer/ipplayer.php", cookies=page.cookies, headers=basic_headers,
                            data={"u": b["s"], "w": "100%25", "h": "500", "s": to_send["data-server"], 'n': '0'})
            res = json.loads(ret.text)
            to_screen(["[debug]Cookie Jar For %s:%s\n" %
                       (ret.url, dict(ret.cookies))], v)
            to_screen(["[debug]Recieved Data:"], v)
            dict_print(res, v)
            data.append(res.get("data").replace("http://", "https://"))
        while len(data) > 3:
            p_print(data)
            dt_n = input(
                "[info]Enter the number of the url to remove from the List:")
            data.pop(int(dt_n)-1)
        if len(data) < 3:
            nones = [None]*(3-len(data))
            data += nones
        if all(s is None for s in data):
            data = []
            print("no urls for episode:", i)
            a = input("Enter URL1:")
            b = input("Enter URL2:")
            if len(b) < 5:
                b = None
            c = input("Enter URL2:")
            if len(c) < 5:
                c = None
            data = [a, b, c]
        episode_data = {**episode_data, i: data}
        to_screen(['[debug]Episode Data'], v)
        dict_print(episode_data, v)
    base_template = (title, image, season, episode_data)
    yn = 'y'
    if yn == 'y':
        print('[info]Adding to database:')
        print(dbmanage.add_to_db(base_template))
    else:
        print("[info]Returning Values Only")
    print("Done")


import getpass


def p_print(el):
    for r in el:
        print("%d. %s" % (el.index(r)+1, r))


def dict_print(el, v=True):
    if v:
        print("{")
        for r in el:
            print("\t%s:%s" % (r, el[r]))
        print("}")


def to_screen(data, v):
    assert isinstance(data, list)
    if v:
        print(*data)
    else:
        return


if __name__ == "__main__":
    number_ = int(input("Enter The Number Of URLs:"))
    verb = input("Enter Verbosity Level(v/s)[v-verbose;s-silent]").lower()

    def url_config(verb):
        url = input("Enter URL:")
        try:
            season = re.search(
                r"-\s*?S(?P<s>\d+", url, re.IGNORECASE).group("s")
        except:
            season = 0
        if verb == 'v':
            verb = True
        else:
            verb = False
            print("[info]Verbosity set to silent")
        n = int(input("Start From Episode Number:"))
        s = input("Season Number-Guess:%s\n" % season)
        return (url, verb, n, s)
    datas = []
    for i in range(1, number_+1):
        datas.append(url_config(verb))
    print("[info]URL List:")
    p_print(datas)
    for t in datas:
        get_(*t)
