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


def get_(url, v=True, n=1, season=0):
    ua = random.choice(
        [
            "Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US) AppleWebKit/604.1.38 (KHTML, like Gecko) Chrome/68.0.3325.162",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0_2 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A421 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 8.1.0; Pixel Build/OPM1.171019.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.137 Mobile Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        ]
    )
    print("[debug]Fetching:\n", url)
    basic_headers = {
        "User-Agent": ua,
        "Upgrade-Insecure-Requests": "1",
        "dnt": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    }
    sess = requests.Session()
    to_screen(["[debug]Using Standard Headers:"], v)
    dict_print(basic_headers, v=v)
    page = sess.get(url, headers=basic_headers, allow_redirects=True)
    to_screen(["[debug]Page URL:", page.url], v)
    to_screen(["[debug]Cookie Jar For %s:" % (page.url)], v)
    dict_print(dict(page.cookies), v)
    soup = bs(page.text, "html.parser")
    to_screen(["\n[debug]Finding Title"], v)
    title = re.search(r"this.page.title\s*?=\s*?'(?P<id>.*?)';", page.text).group("id")
    to_screen(["[debug]Found:", title], v)
    to_screen(["[debug]Finding Thumbnail"], v)
    thumbnail = soup.find("meta", attrs={"property": "og:image"}).attrs.get("content")
    to_screen(["[debug]Found", thumbnail], v)
    if thumbnail.startswith("/"):
        if thumbnail.startswith("//"):
            thumbnail = "https:" + thumbnail
        else:
            thumbnail = input("fix the thumbnail:")
    next_episode = True
    episode_data = {}
    i = 1
    while next_episode:
        data = []
        data = None
        data = []
        urls = soup.find_all(attrs={"episode-data": str(i)})
        if len(urls) == 0:
            next_episode = False
            break
        for url in urls:
            data.append(url.attrs.get("player-data").replace("http://", "https://"))
        if len(data) < 3:
            nones = [None] * (3 - len(data))
            data += nones
        p_print(data)
        dt_n = input(
            "[info]Enter the number of the numbers of urls seperated by spaces:"
        )
        dt_n = dt_n.split()
        print(dt_n)
        to_remove = []
        for num in dt_n:
            to_remove.append(data[int(num) - 1])
        data = list(set(data) - set(to_remove))
        if len(data) < 3:
            nones = [None] * (3 - len(data))
            data += nones
        p_print(data)
        episode_data = {**episode_data, i: data}
        i += 1
        to_screen(["[debug]Episode Data"], v)
        dict_print(episode_data, v)
    to_screen(["[debug]Fetching Thumbnail and uploading to cdn"], v)
    image = upload.upload(thumbnail).get("secure_url")
    to_screen(["[debug]Secure URL of Image:", image], v)
    base_template = (title, image, season, episode_data)
    yn = "y"
    if yn == "y":
        print("[info]Adding to database:")
        print(base_template)
        print(dbmanage.add_to_db(base_template))


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
    number_ = int(input("Enter The Number Of URLs:"))
    verb = input("Enter Verbosity Level(v/s)[v-verbose;s-silent]").lower()

    def url_config(verb):
        url = input("Enter URL:")
        if verb == "v":
            verb = True
        else:
            verb = False
            print("[info]Verbosity set to silent")
        n = 1
        s = input("Season Number:")
        return (url, verb, n, s)

    datas = []
    for i in range(1, number_ + 1):
        datas.append(url_config(verb))
    print("[info]URL List:")
    p_print(datas)
    for t in datas:
        get_(*t)
