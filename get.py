import base64
import hashlib
import json
import os
import random
import re
import secrets
import shutil
import threading
import time
import uuid
from urllib.parse import quote, unquote, urlparse

from bs4 import BeautifulSoup as bs
from flask_sqlalchemy import SQLAlchemy

# import psycopg2
from quart import (
    Quart,
    Response,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    websocket,
)

try:
    import api.ippl_api as ippl_api
except ImportError:
    pass
from dbmanage import req_db
from set_env import set_env_vars

set_env_vars()
json_ctype = "application/json"
app = Quart(__name__)
app.config["FORCE_HTTPS_ON_PROD"] = True
app.secret_key = os.environ.get("db_pass_insig")

sanitize_str = lambda movie: re.sub(r"([^\w]|_)", "", movie).lower()


def open_and_read(fn: str, mode: str = "r", strip: bool = True):
    with open(fn, mode) as f:
        if strip:
            data = f.read().strip()
        else:
            data = f.read()
    return data


def open_and_write(fn: str, mode: str = "w", data=None) -> None:
    with open(fn, mode) as f:
        f.write(data)
    return


try:
    dburl = os.environ.get("DATABASE_URL")
except:
    raise Exception("No DB url specified try add it to the environment")
app.config["SQLALCHEMY_DATABASE_URI"] = dburl
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/66.0.3343.3 Safari/537.36"


# start WEB
scripts_dir = os.path.join(app.root_path, "static", "dist")
if not os.path.isdir(scripts_dir):
    os.mkdir(scripts_dir)


def from_cache_or_save(mid):
    if not os.path.isdir(".player-cache"):
        os.mkdir(".player-cache")
    file_path = os.path.join(".player-cache", mid + ".json")
    data: dict = None
    if os.path.isfile(file_path):
        try:
            data = json.loads(open_and_read(file_path))
        except:
            data = None
    if data:
        return data
    meta = tvData.query.filter_by(mid=mid).first()
    if not meta:
        return None
    data_js = {
        "movie_name": meta.moviedisplay,
        "thumbnail": meta.thumb,
        "episodes": meta.episodes,
        "episode_meta": len(meta.episodes),
        "season": meta.season,
    }
    open_and_write(file_path, "w", data=json.dumps(data_js))
    return data_js


def get_all_results(req_if_not_heroku=True, number=0, shuffle=True, url=None):
    db_cache_file = os.path.join(app.root_path, ".db-cache--all")
    jsdata = show_data = []
    data = None
    if os.path.isfile(db_cache_file):
        _data = open_and_read(db_cache_file)
        try:
            data = json.loads(_data).get("data").get("movies")
            show_data = data
        except Exception as e:
            print(e)
    elif True:
        print("Fetching Data")
        _data = tvData.query.all()
        for url in _data:
            jsdata.append(
                {
                    "movie": url.moviedisplay,
                    "id": url.mid,
                    "thumb": url.thumb,
                    "moviename": url.movie,
                }
            )
        _meta = json.dumps({"stamp": time.time(), "data": {"movies": jsdata}})
        open_and_write(db_cache_file, "w", _meta)
        show_data = jsdata
    else:
        return []
    if number:
        return random.choices(show_data, k=number)
    if shuffle:
        random.shuffle(show_data)
        return show_data


def generate_id() -> str:
    lst_ = secrets.token_urlsafe()
    return lst_[: gen_rn()]


def gen_rn() -> int:
    return random.randint(12, 17)


def is_heroku(url):
    parsedurl = urlparse(url).netloc
    return (
        "127.0.0.1" not in parsedurl
        or "localhost" not in parsedurl
        or "192.168." not in parsedurl
    ) and ("herokuapp" in parsedurl or "ws://app_server/" in url)


# pylint: disable=E1101


class tvData(db.Model):
    mid = db.Column(db.String, primary_key=True)
    movie = db.Column(db.String(100))
    moviedisplay = db.Column(db.String(100))
    season = db.Column(db.String(3))
    episodes = db.Column(db.PickleType)
    thumb = db.Column(db.String(1000))

    def __init__(self, movie, thumb, season, episodes):
        self.mid = generate_id()
        self.season = season
        self.episodes = episodes
        self.movie = sanitize_str(movie)
        self.moviedisplay = movie
        self.thumb = thumb

    def __repr__(self):
        return "<Name %r>" % self.movie


class DataLytics(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    actions = db.Column(db.PickleType)
    _type = db.Column(db.String(100))

    def __init__(self, _type, act):
        self.actions = act
        self._type = _type

    def __repr__(self):
        return f"<DATA-ID:{self.idx}>"


class tvRequests(db.Model):
    r_id = db.Column(db.Integer, primary_key=True)
    movie = db.Column(db.String(100))
    url = db.Column(db.String(1000))

    def __init__(self, movie, url=None):
        self.movie = movie
        self.url = url

    def __repr__(self):
        return "<Name %r>" % self.movie


class deadLinks(db.Model):
    r_id = db.Column(db.Integer, primary_key=True)
    movieid = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    def __init__(self, movie_id, name=None):
        self.movieid = movie_id
        self.name = name

    def __repr__(self):
        return "<Name %r>" % self.movieid


# pylint: enable=E1101


@app.route("/robots.txt")
async def check__():
    return await send_from_directory(
        os.path.join(app.root_path, "static"), "robots.txt"
    )


@app.route("/")
async def index():
    if is_heroku(request.url):
        return redirect("https://tv.pycode.tk/", status_code=301)
    return "test"


def movie_list_sort(md: tvData) -> str:
    return md.movie


@app.route("/api/get-all/", methods=["POST"])
async def get_all_results_api():
    movs = get_all_results(shuffle=True, url=request.url)
    data = {"movies": movs}
    return Response(json.dumps(data), content_type=json_ctype)


@app.route("/api/get-show-metadata/", methods=["POST"])
async def get_show_meta():
    data = await request.get_json()
    idx = data.get("id")
    meta = from_cache_or_save(idx) if idx else None
    if not meta:
        return Response(json.dumps({"error": "404"}), content_type=json_ctype)
    return Response(
        json.dumps(
            {
                "movie_name": meta.get("movie_name"),
                "episode_meta": meta.get("episode_meta"),
            }
        ),
        content_type=json_ctype,
    )


@app.route("/api/data/search/", methods=["POST"])
async def serchs():
    json_data = {}
    form = await request.form
    json_data["movies"] = []
    q = sanitize_str(form["q"])
    if not q:
        return json.dumps({"no-res": True})
    print("Search For:", q)
    urls = tvData.query.filter(
        tvData.movie.op("~")(r"(?s).*?%s" % (re.escape(q)))
    ).all()
    urls.sort(key=movie_list_sort)
    for url in urls:
        json_data["movies"].append(
            {"movie": url.moviedisplay, "id": url.mid, "thumb": url.thumb}
        )
    if len(json_data["movies"]) == 0:
        return json.dumps({"no-res": True})
    return Response(json.dumps(json_data), content_type=json_ctype)


@app.route("/favicon.ico")
async def send_fav():
    return await send_from_directory(
        os.path.join(app.root_path, "static"), "favicon.ico"
    )


@app.route("/api/build-player/ep/", methods=["POST"])
async def send_ep_data():
    eeid = await request.get_json()
    eid = str(eeid["eid"])
    episode = eeid["mid"]
    data = from_cache_or_save(episode)
    if not data:
        return Response(json.dumps({"error": "no-eps"}))
    episodes = data.get("episodes")
    urls = episodes.get(int(eid)) or episodes.get(eid)
    json_data = {
        "url": str(urls[0]).replace("http:", "https:") if urls[0] else None,
        "alt1": str(urls[1]).replace("http:", "https:") if urls[1] else None,
        "alt2": str(urls[2]).replace("http:", "https:") if urls[2] else None,
    }
    res = await make_response(json.dumps(json_data))
    res.headers["Content-Type"] = json_ctype
    return res


@app.route("/media/add-shows/fetch/")
async def search_shows():
    show = request.args.get("s")
    return Response(ippl_api.main_(term=show), content_type=json_ctype)


@app.after_request
async def resp_headers(resp):
    if "localhost" in request.headers.get("origin", ""):
        resp.headers["access-control-allow-origin"] = request.headers["origin"]
    else:
        resp.headers["access-control-allow-origin"] = "https://tv.pycode.tk"
    resp.headers["Access-Control-Allow-Headers"] = request.headers.get(
        "Access-Control-Request-Headers", "*"
    )
    resp.headers["access-control-allow-credentials"] = "true"
    return resp


@app.route("/i/rec/")
async def recommend():
    # __import__("time").sleep(5)
    data = get_all_results(False, number=5, shuffle=False, url=request.url)
    rec = json.dumps({"recommendations": data})
    return Response(rec, content_type=json_ctype)


@app.websocket("/suggestqueries")
async def socket_conn():
    sort_dict = lambda x: x.get("movie")
    while 1:
        _query: str = await websocket.receive()
        query = re.escape(sanitize_str(_query))
        if not query:
            await websocket.send(json.dumps({"no-res": True}))
            continue
        json_data = {"data": []}
        req_if_heroku: bool = False
        if is_heroku(websocket.url):
            req_if_heroku = True
        names: list = get_all_results(
            req_if_not_heroku=req_if_heroku, url=websocket.url
        )
        json_data["data"] = [s for s in names if re.search(query, s["moviename"])]
        if not len(json_data["data"]):
            await websocket.send(json.dumps({"no-res": True}))
        else:
            json_data["data"].sort(key=sort_dict)
            await websocket.send(json.dumps(json_data))


@app.route("/api/add/tv-show/lookup")
async def add_show_lookup():
    _show_url = request.args.get("s")
    title = request.args.get("t", "")
    q = sanitize_str(title)
    urls = tvData.query.filter(tvData.movie.op("~")(r"(?s).*?%s" % (q))).all()
    if len(urls) > 0:
        return (
            "We already have a show with similar name..to prevent multiple copies of the same show..please request this show to be manually added",
            403,
        )
    thread = threading.Thread(
        target=ippl_api.get_, args=(_show_url, title, True, 1, 0, db, tvData)
    )
    thread.start()
    return f"Adding {title}"


@app.route("/api/site-select/")
async def redir_data():
    site = session.get("site-select", "None")
    return Response(json.dumps({"site": site}), content_type=json_ctype)


@app.route("/set-downloader/")
async def set_dl():
    session["site-select"] = request.args.get("dl")
    return redirect(session["site-select"], status_code=301)


@app.route("/collect/", methods=["POST", "GET"])
async def collect():
    return ""


@app.route("/beacon-test", methods=["POST"])
async def bcontest():
    await request.data
    return ""


# for heroku nginx
@app.before_serving
def open_to_nginx():
    try:
        open("/tmp/app-initialized", "w").close()
    except:
        pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, use_reloader=True)

