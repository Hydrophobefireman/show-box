import requests
import re
from bs4 import BeautifulSoup as bs
from urllib.parse import quote_plus as quote
import ippl


def main_(term: str = None, s_url: str = None) -> None:
    if s_url is None:
        if term is None:
            return "No term Supplied"
        url = "https://solarmoviesonline.net/search/%s.html" % (quote(term))
    else:
        url = s_url
    ua = "Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US) AppleWebKit/604.1.38 (KHTML, like Gecko) Chrome/68.0.3325.162"
    print("[debug]Fetching:\n", url)
    basic_headers = {
        "User-Agent": ua,
        "Upgrade-Insecure-Requests": "1",
        "dnt": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    }
    sess = requests.Session()
    htm = sess.get(url, headers=basic_headers, allow_redirects=True)
    page = htm.text
    soup = bs(page, "html.parser")
    atags = soup.find_all(attrs={"data-jtip": True})
    for tag in atags:
        u = tag.attrs.get("href")
        if u:
            yn = input("Should I add:%s ?\n" % (u)).lower()
            if yn == "y":
                print("[info]Adding:", u)
                if tag.findChild(attrs={"class": "mli-eps"}):
                    print(ippl.get_(u, True))
            else:
                print("[info] Not adding the movie")


if __name__ == "__main__":
    url = input("Enter The URL or Leave it Blank:")
    if len(url) < 1:
        print(main_(input("No URL supplied.\nEnter The Term:")))
    else:
        print(main_(s_url=url))
