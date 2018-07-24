import json
import random
import re
from time import sleep
from urllib.parse import urlencode
from urllib.parse import urlparse as urlp_

import requests
from bs4 import BeautifulSoup as bs

import dbmanage
import upload


class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_(url, v=True, n=1, season=0):
    ua = random.choice(
        [
            "Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US) AppleWebKit/604.1.38 (KHTML, like Gecko) Chrome/68.0.3325.162",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0_2 like Mac OS X) AppleWebKit /604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A421 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 8.1.0; Pixel Build/OPM1.171019.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.137 Mobile Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Like Gecko Firefox/57.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        ]
    )
    print(colors.OKBLUE+"[debug]"+colors.ENDC+"Fetching:\n", url)
    basic_headers = {
        "User-Agent": ua,
        "Upgrade-Insecure-Requests": "1",
        "dnt": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    }
    sess = requests.Session()
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
               "Using Standard Headers:"], v)
    dict_print(basic_headers, v=v)
    page = sess.get(url, headers=basic_headers, allow_redirects=True)
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC+"Page URL:", page.url], v)
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
               "Cookie Jar For %s:" % (page.url)], v)
    dict_print(dict(page.cookies), v)
    soup = bs(page.text, "html.parser")
    to_screen(["\n"+colors.OKBLUE+"[debug]"+colors.ENDC+"Finding Title"], v)
    title = soup.find("input", attrs={"name": "movies_title"}).attrs["value"]
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC+"Found:", title], v)
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC+"Finding Thumbnail"], v)
    thumbnail = soup.find("input", attrs={"name": "phimimg"}).attrs["value"]
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC+"Found", thumbnail], v)
    if thumbnail.startswith("/"):
        if thumbnail.startswith("//"):
            thumbnail = "https:" + thumbnail
        else:
            thumbnail = input("fix the thumbnail:")
    url_ = page.url
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
               "Adding Referer to headers"], v)
    basic_headers = {**basic_headers, "Referer": url_}
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
               "Adding X-Requested-With to headers"], v)
    basic_headers = {**basic_headers, "X-Requested-With": "XMLHttpRequest"}
    parsed_url = urlp_(url_)
    origin = "https://" + parsed_url.netloc
    host = origin + "/"
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
               "Adding Origin to headers"], v)
    basic_headers = {**basic_headers, "Origin": origin}
    div = soup.find(attrs={"id": "list-eps"}
                    ) or soup.find(attrs={"class": "pas-list"}) or soup.find(attrs={"id": "ip_episode"})
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
               "Finding Ipplayer Configs"], v)
    if div is None:
        raise Exception("Could Not Find Ipplayer Configs")
    tags = div.findChildren(attrs={"data-next": True})
    number_of_eps = len(tags)
    episode_data = {}
    for i in range(n, number_of_eps + 1):
        attrs_ = tags[i - 1]
        to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
                   "Fetching Config URLs for episode number:", i], v)
        data_headers = {
            "keyurl": "%d" % (i),
            "postid": "server",
            "phimid": attrs_.attrs["data-film"],
        }
        to_screen(["\n"+colors.OKBLUE+"[debug]" +
                   colors.ENDC+"Sending Config:"], v)
        dict_print(data_headers, v)
        toparse = sess.post(host + "index.php",
                            data=data_headers, cookies=page.cookies)
        parsed_data = bs(toparse.text, "html.parser")
        tgs = parsed_data.find_all("a")
        data = []
        for t in tgs:
            to_send = t.attrs
            if "netu.tv" in t.text.lower() or 'hqq.tv' in t.text.lower():
                print(colors.FAIL+"[info]"+colors.ENDC +
                      "Stopping Execution,found a malacious website")
                continue
            to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
                       "Working with the configs of", t.string], v)
            to_screen([colors.OKBLUE+"[debug]" +
                       colors.ENDC+"Found Configs:"], v)
            dict_print(t.attrs, v)
            sleep(1)
            a = sess.post(
                host + "ip.file/swf/plugins/ipplugins.php",
                headers=basic_headers,
                data={
                    "ipplugins": 1,
                    "ip_film": to_send["data-film"],
                    "ip_server": to_send["data-server"],
                    "ip_name": to_send["data-name"],
                    "fix": "null",
                },
            )
            b = json.loads(a.text)
            sleep(1)
            to_screen([colors.OKBLUE+"[debug]"+colors.ENDC+"Recieved:"], v)
            dict_print(b, v)
            ret = sess.post(
                host + "ip.file/swf/ipplayer/ipplayer.php",
                cookies=page.cookies,
                headers=basic_headers,
                data={
                    "u": b["s"],
                    "w": "100%25",
                    "h": "500",
                    "s": to_send["data-server"],
                    "n": "0",
                },
            )
            res = json.loads(ret.text)
            to_screen(
                [colors.OKBLUE+"[debug]"+colors.ENDC+"Cookie Jar For %s:%s\n" %
                    (ret.url, dict(ret.cookies))], v
            )
            to_screen([colors.OKBLUE+"[debug]" +
                       colors.ENDC+"Recieved Data:"], v)
            dict_print(res, v)

            url_rec = res.get("data")
            if url_rec:
                if "netu.tv" in url_rec or "hqq.tv" in url_rec:
                    # Garbage website..mines crypto and stuff ,terrible hosting videos are usually deleted and other stuff
                    # stay away from this abomination of video hosting
                    print(colors.FAIL+"[info]"+colors.ENDC +
                          "Stopping Execution,found a malacious website")
                    continue
                data.append(url_rec.replace("http://", "https://"))
            else:
                print(colors.BOLD+"[info]"+colors.ENDC+"Stopping Execution")
                continue
        while len(data) > 3:
            p_print(data)
            dt_n = input(
                colors.BOLD+"[info]"+colors.ENDC+"Enter the number of the url to remove from the List:")
            data.pop(int(dt_n) - 1)
        if len(data) < 3:
            nones = [None] * (3 - len(data))
            data += nones
        if all(s is None for s in data):
            data = []
            print(colors.BOLD+"[info]"+colors.ENDC+"no urls for episode:", i)
            a = input("Enter URL1:")
            b = input("Enter URL2:")
            if len(b) < 5:
                b = None
            c = input("Enter URL2:")
            if len(c) < 5:
                c = None
            data = [a, b, c]
        episode_data = {**episode_data, i: data}
        to_screen([colors.OKBLUE+"[debug]"+colors.ENDC+"Episode Data"], v)
        dict_print(episode_data, v)
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
               "Fetching Thumbnail and uploading to cdn"], v)
    image = upload.upload(thumbnail).get("secure_url")
    to_screen([colors.OKBLUE+"[debug]"+colors.ENDC +
               "Secure URL of Image:", image], v)
    base_template = (title, image, season, episode_data)
    yn = "y"
    if yn == "y":
        print(colors.BOLD+"[info]"+colors.ENDC+"Adding to database:")
        print(dbmanage.add_to_db(base_template))
    else:
        print(colors.BOLD+"[info]"+colors.ENDC+"Returning Values Only")
    print("Done")


def p_print(el):
    for r in el:
        print("%d. %s" % (el.index(r) + 1, r))


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
    number_ = int(input(colors.BOLD+"Enter The Number Of URLs:"+colors.ENDC))
    verb = input("Enter Verbosity Level(v/s)[v-verbose;s-silent]").lower()

    def url_config(verb):
        url = input("Enter URL:")
        if verb == "v":
            verb = True
        else:
            verb = False
            print(colors.BOLD+"[info]"+colors.ENDC+"Verbosity set to silent")
        n = 1
        s = input("Season Number:")
        return (url, verb, n, s)

    datas = []
    for i in range(1, number_ + 1):
        datas.append(url_config(verb))
    print(colors.BOLD+"[info]"+colors.ENDC+"URL List:")
    p_print(datas)
    for t in datas:
        get_(*t)
