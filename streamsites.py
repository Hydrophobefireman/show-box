import json
import re
from urllib.parse import urlparse

import requests
import base64
from bs4 import BeautifulSoup as bs


def check_for_stream_sites(url, ua):
    s_sites = ["coolseries.video", "watchseries.",
               "watch-series", "tvzion", "putlocker"]
    data = False
    if any(a in url for a in s_sites):
        if re.search(r"https?://.*?coolseries\.", url) is not None:
            data = cool_series(url, ua)
        if re.search(r"https?://.*watch.?series", url) is not None:
            data = watchseries(url, ua)
        if re.search(r"https?://.*?tvzion", url) is not None:
            data = tvzion(url, ua)
        if re.search(r"https?://.*?putlocker", url) is not None:
            print("try")
            data = list(
                set([s for s in putlocker(url, ua) if urlcheck(s)]))
        return data
    else:
        # if urlcheck(url)[0]:  # Not a streaming site
        return False


def putlocker(url, ua):
    source = requests.get(url, headers={"User-Agent": ua}).text
    # too many rip off sites..gotta support some of em
    ret = source

    def searches(url, source):
        try:
            g = re.findall(r"((?<=src:\s').*?(?=\',))", source)
            if "embed/" in str(g):
                print(g[0])
                d = requests.get(urlparse(url).scheme+"://" +
                                 urlparse(url).netloc+g[0]).text
                url = bs(d, "html.parser").find("iframe").attrs.get('src')
                print(url)
                if url:
                    return [url]
            print("pid")
        except:
            pass
        try:
            p_id = re.findall(r"((?<=post_id\":\").*?(?=\"}))", source)[0]
            data_src = json.loads(requests.post(urlparse(url).scheme+"://"+urlparse(url).netloc + "/wp-admin/admin-ajax.php", data={
                "action": "get_oload_gs", "post_id": p_id}).text).get("src")
            return [data_src]
        except Exception as e:
            print(e)
            pass
        try:
            res = [s for s in re.findall(
                r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+', source) if "http" in s]
            print(len(res))
            data = [s for s in res if urlcheck(s)[0]]
            print(data)
            return data
        except Exception as e:
            return False
        # looks terrible but there are a few 100 putlocker domains around this supports most of them except one
    res = searches(url, source)
    print(res)
    if len(res) == 0 or res is False:
        try:
            parsed_url = urlparse(url)
            base_url_check = parsed_url.scheme+"://"+parsed_url.netloc+"/tmp_chk.php"
            requests.post(base_url_check, data={"tst": parsed_url.netloc})
            source = requests.post(url, data={"tmp_chk": 1}).text
            res = searches(url, source)
            if len(res) == 0 or res is False:
                raise Exception("No Data")
        except Exception as e:
            try:
                print("B64")
                decoded_links = []
                print(e)

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
                        page = requests.get(l, headers={"User-Agent": ua}).text
                        b64decoder(decoded_links, page)
                if len(decoded_links) > 0:
                    return decoded_links
                return False
            except Exception as e:
                return False
    return res


def tvzion(url, ua):
    _test = [
        'https://www2.tvzion.com/watch-the-office-season-3-episode-14-s03e14-online3-free-v1-2316']
    source = requests.get(url, headers={"User-Agent": ua}).text
    source = re.sub(r"\s", '', source)
    data = []
    videoreg = r"((?<=rel=\"video_src\"href=\").*?(?=\"))"
    video = re.findall(videoreg, source)
    sess = requests.Session()
    video = sess.head(
        video[0], headers={"User-Agent": ua, "Referer": url}, allow_redirects=True).url
    if urlcheck(video):
        data.append(video)
        return data
    else:
        return False


def watchseries(url, ua):  # general extractor
    source = requests.get(url, headers={"User-Agent": ua}).text
    urls = re.findall(r"https?://.*?(?=\")", source)
    data = []
    for u in urls:
        if "/external/" in u:
            u = get_final_url(u, ua, url)
            if u:
                data += u  # we need one list only
        if urlcheck(u):
            data.append(u)
    return data


def get_final_url(u, ua, url):
    hosts = extract_host(url)
    source = requests.get(u, headers={"User-Agent": ua, "Referer": url}).text
    urls = re.findall(
        r'(?:(?:https?|ftp)?:\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+', source)
    data = []
    for u in urls:
        if extract_host(u) != hosts:
            if u.startswith("//"):
                u = "http:"+u
            if urlcheck(u):
                data.append(u)
    return data


def extract_host(url):
    if re.search("https?://", url) is None:
        hosts = url.split("/")[0]
    else:
        hosts = url.split("://")[1].split("/")[0]
    return hosts


def cool_series(url, ua):
    data = requests.get(url, headers={"User-Agent": ua}).text
    data = re.sub(r"[\s]", '', data)
    regex = r'((?<=<IFRAMESRC=").*?(?="\w?))'
    iframes = [s for s in re.findall(
        regex, data, re.IGNORECASE) if "http" in s and "vidfast" not in s]
    g_urls = []
    for url in iframes:
        hts = bs(requests.get(url, headers={
            "User-Agent": ua, "Referer": url, "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"}).text, "html.parser")
        iframeurl = hts.findAll("iframe")[0].attrs['src']
        if urlcheck(iframeurl):
            g_urls.append(iframeurl)
    return g_urls


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
