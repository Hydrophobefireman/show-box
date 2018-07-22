import base64
import json
import re
import traceback
from urllib.parse import urlparse
from warnings import warn

import requests
from bs4 import BeautifulSoup as bs

import ippl
import streamsites

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3343.3 Safari/537.36"


def scrape(url):
    base_url = url
    warn("Some Go Movies url need a /watching.html in the end. Remember to add it if needed")
    req = requests.get(url, headers={"User-Agent": USER_AGENT})
    page = req.text
    soup = bs(page, 'html.parser')
    content_div = soup.findAll(
        attrs={"class": 'les-content'})
    if len(content_div) == 0:
        content_div = soup.findAll(attrs={"id": 'les-content'})
    dv = []
    for div in content_div:
        data = les_content_parser(div)
        if data:
            dv += data
    if dv:
        return dv
    url = re.search(r"var\s*locations\s?=\s?.*?(?<=;)",
                    url, re.IGNORECASE)
    if url:
        return [url.group()]
    urls = iframe_src_or_none(soup)
    if urls:
        return urls
    ippl_try = try_ipplayer_search(base_url)
    if ippl_try:
        return ippl_try
    regs = re.search(r"id:\s?\"(?P<id>.*?)\"", page)
    if regs:
        v_id = regs.group('id')
        print(v_id)
        data_r = try_get_ajax(base_url, v_id)
        if data_r:
            print(data_r)
            return data_r
    else:
        data__ = None
        try:
            data__ = streamsites.check_for_stream_sites(base_url, USER_AGENT)
            if data__:
                return data__
        except:
            pass
        data = b64_try(page)
        if data:
            return data


def try_ipplayer_search(url):
    try:
        return ippl.get_(url, v=True)
    except:
        return None


def try_get_ajax(url, id_):
    parsed_url = urlparse(url)
    host = "http://"+parsed_url.netloc+"/"
    url1 = host+"ajax/movie_episodes/"+id_
    basic_headers = {
        "User-Agent": USER_AGENT,
        "Upgrade-Insecure-Requests": "1",
        "dnt": '1',
        "referer": url,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
    }
    data = requests.Session().get(url1, headers=basic_headers).text
    print("[debug]Recieved Data of length:", len(data))
    try:
        htm = json.loads(data)['html']
    except:
        return False
    soup = bs(htm, 'html.parser')
    srcs = []
    divs = soup.findAll('a', attrs={"data-id": True})
    for div in divs:
        d_id = div.attrs.get("data-id")
        url_2 = host+"ajax/movie_embed/"+d_id
        print("[debug]Requesting:", url_2)
        try:
            txt = json.loads(requests.Session().get(
                url_2, headers=basic_headers).text)
            print("[debug]Recieved:", txt)
            if str(txt['status']) == '1':
                srcs.append(txt['src'])
        except Exception as e:
            print(e)
            # raise e
            continue
    if len(srcs) == 0:
        return None
    return srcs


def les_content_parser(div):
    # Find all urls
    reg = r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+'
    urls = re.findall(reg, str(div))
    valid_urls = [s for s in urls if urlcheck(s)]
    if valid_urls:
        return valid_urls
    else:
        return None


def urlcheck(url):
    if re.search(r"^(https?:)?//.*\.?((docs|drive)\.google.com)|video\.google\.com", url, re.IGNORECASE) is not None:
        return True
    if re.search(r"^(https?:)?//.*\.?(photos\.google|photos\.app\.goo\.gl)", url, re.IGNORECASE) is not None:
        return True
    if re.search(r"^(https?:)?//.*\.?estream", url, re.IGNORECASE) is not None:
        return True
    if re.search(r"^(https?:)?//.*\.?vidzi\.", url, re.IGNORECASE) is not None:
        return True
    if re.search(r"^(https?:)?//.*\.?yourupload\.", url, re.IGNORECASE) is not None:
        return True
    if re.search(r"^(https?:)?//.*\.?dailymotion\.", url, re.IGNORECASE) is not None:
        return True
    if re.search(r"^(https?:)?//.*\.?watcheng\.", url, re.IGNORECASE) is not None:
        return True
    if re.search(r"^(https?:)?//.*\.?rapidvideo\.", url, re.IGNORECASE) is not None:
        return True
    if re.search(r"^(https?:)?//.*\.?megadrive\.", url, re.IGNORECASE) is not None:
        return True
    if re.search(r"^(https?:)?//(.{3})?\.?(oload|openload|daclips|thevideo|vev.io|streamango|streamago|streamcloud)", url, re.IGNORECASE) is not None:
        return True
    else:
        return False


def iframe_src_or_none(page):
    iframe = page.findAll("iframe", attrs={"src": True})
    data = []
    reg = r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+'
    for fr in iframe:
        if len(fr.attrs.get("src")) < 1:
            continue
        print("Found an Iframe url")
        f = fr.attrs['src']
        if "kizyplayer" in f:
            print("Using Kizy Player")
            if f.startswith("//"):
                f = "http:"+f
            source = requests.get(f, headers={"User-Agent": USER_AGENT}).text
            url = re.search(
                r"addiframe\(('|\")(?P<url>.*?)('|\"),", source, re.IGNORECASE)
            if url:
                url = url.group('url')
                if url.startswith("//"):
                    url = 'http:'+url
                print("Fetching:", url)
                source = requests.get(url, headers={
                    "User-Agent": USER_AGENT, "Referer": f}).text
                urls = re.findall(r"(?s)file:\s?['|\"].*?['|\"],", source)
                for r in urls:
                    data.append(re.search(reg, r).group())
                return data
    return None


def b64_try(source):
    ret = source

    def b64decoder(decoded_links, source):
        print("b64decoder")
        reg = re.search(
            r"base64.decode\((\"|')(?P<id>.*?)(\"|')\)", source, re.IGNORECASE)
        if reg:
            reg = base64.b64decode(
                reg.group("id").encode()).decode()
            reg = re.search(
                r'(?:(?:https?|ftp)?:\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+', reg).group()
            decoded_links.append(reg)
    try:
        decoded_links = []
        b64decoder(decoded_links, source)
        soup = bs(ret, 'html.parser')
        ptags = soup.find_all("p", attrs={"class": "server_play"})
        links = []
        if len(ptags) > 0:
            print('PTAGS', ptags)
            ptags = ptags[:10]
            for p in ptags:
                atag = p.findChild("a")
                print(atag)
                if atag:
                    links.append(atag.attrs.get("href"))
        print(links)
        for l in links:
            if l:
                page = requests.get(l, headers={"User-Agent": USER_AGENT}).text
                b64decoder(decoded_links, page)
        if len(decoded_links) > 0:
            return [s for s in decoded_links if urlcheck(s)]
        return False
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        return False


if __name__ == '__main__':
    print(scrape(input("url:")))
