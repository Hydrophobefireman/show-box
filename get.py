import base64
import json
import os
import random
import re
import secrets
import threading
import time
import uuid
from urllib.parse import quote, unquote, urlparse

# import psycopg2
from quart import (
    Quart,
    Response,
    make_response,
    redirect,
    websocket,
    render_template,
    request,
    send_from_directory,
    session,
)
from flask_sqlalchemy import SQLAlchemy
from htmlmin.minify import html_minify
from api import ippl_api
from dbmanage import req_db

from flask_tools import flaskUtils

app = Quart(__name__)
app.config["FORCE_HTTPS_ON_PROD"] = True
dburl = os.environ.get("DATABASE_URL")
flaskUtils(app=app)


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


app.secret_key = os.environ.get("db_pass_insig") or open_and_read(
    ".dbpass-insignificant_1"
)


try:
    dburl = os.environ.get("DATABASE_URL") or open_and_read(".dbinfo_")
except:
    raise Exception(
        "No DB url specified try add it to the environment or \
        create a .dbinfo_ file with the url"
    )
app.config["SQLALCHEMY_DATABASE_URI"] = dburl
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/66.0.3343.3 Safari/537.36"


def get_all_results(request_if_not_heroku=True, number=0, shuffle=True):
    db_cache_file = os.path.join(app.root_path, ".db-cache--all")
    jsdata = __data__ = []
    data = None
    if os.path.isfile(db_cache_file):
        _data = open_and_read(db_cache_file)
        try:
            data = json.loads(_data).get("data").get("movies")
            __data__ = data
        except Exception as e:
            print(e)
    elif request_if_not_heroku:
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
        __data__ = jsdata
    else:
        return []
    if number:
        return random.choices(__data__, k=number)
    if shuffle:
        random.shuffle(__data__)
        return __data__


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
        self.movie = re.sub(r"([^\w]|_)", "", movie.lower())
        self.moviedisplay = movie
        self.thumb = thumb

    def __repr__(self):
        return "<Name %r>" % self.movie


def generate_id() -> str:
    lst_ = secrets.token_urlsafe()
    return lst_[: gen_rn()]


def gen_rn() -> int:
    return random.randint(10, 17)


def is_heroku(url):
    parsedurl = urlparse(url).netloc
    return (
        "127.0.0.1" not in parsedurl
        or "localhost" not in parsedurl
        or "192.168." not in parsedurl
    ) and "herokuapp" in parsedurl


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


@app.route("/robots.txt")
async def check__():
    return await send_from_directory(
        os.path.join(app.root_path, "static"), "robots.txt"
    )


@app.route("/")
async def index():
    if session.get("req-data"):
        d = "Thanks for helping us out!"
    else:
        d = " "
    return html_minify(await render_template("index.html", msg=d))


@app.route("/report/")
async def report_dead():
    m_id = request.args.get("id")
    if m_id is None:
        return "No movie id specified"
    meta_ = tvData.query.filter_by(mid=m_id).first()
    if meta_ is None:
        return "No movie associated with given id"
    thumb = meta_.thumb
    title = meta_.moviedisplay
    return await render_template(
        "link-report.html", m_id=m_id, title=title, thumb=thumb
    )


@app.route("/submit/report/", methods=["POST"])
async def parse_report():
    try:
        form = await request.form
        mid = form["id"]
        col = deadLinks(mid)
        db.session.add(col)
        db.session.commit()
        return "Response recorded.Thank You for your help!"
    except Exception as e:
        print(e)
        return "An unknown error occured during processing your request"
    # raise e


@app.route("/search")
async def send_m():
    if request.args.get("q") is None or not re.sub(
        r"([^\w]|_)", "", request.args.get("q")
    ):
        return "Specify a term!"
    q = request.args.get("q")

    return html_minify(await render_template("movies.html", q=q))


@app.route("/help-us/")
async def ask_get():
    return html_minify(await render_template("help.html"))


@app.route("/db-manage/parse-requests/", methods=["POST"])
async def get_s():
    _movie = await request.form
    movie = _movie.get("movie")
    if not re.sub(r"([^\w]|_)", "", movie):
        print("No movie Given")
        return "Please mention the movie"
    url = _movie.get("url")
    data = (movie, url)
    a = req_db(data)
    print(a)
    return redirect("/", status_code=301)


@app.route("/googlef06ee521abc7bdf8.html")
async def google_():
    return "google-site-verification: googlef06ee521abc7bdf8.html"


def movie_list_sort(md: tvData) -> str:
    return md.movie


@app.route("/data/search/", methods=["POST"])
async def serchs():
    json_data = {}
    form = await request.form
    json_data["movies"] = []
    q = re.sub(r"([^\w]|_)", "", form["q"]).lower()
    print("Search For:", q)
    urls = tvData.query.filter(tvData.movie.op("~")(r"(?s).*?%s" % (q))).all()
    urls.sort(key=movie_list_sort)
    for url in urls:
        json_data["movies"].append(
            {"movie": url.moviedisplay, "id": url.mid, "thumb": url.thumb}
        )
    if len(json_data["movies"]) == 0:
        return json.dumps({"no-res": True})
    return Response(json.dumps(json_data), content_type="application/json")


@app.route("/error-configs/")
async def err_configs():
    return await render_template("err.html")


@app.route("/all/")
async def all_movies():
    session["req-all"] = (generate_id() + generate_id())[:20]
    return html_minify(await render_template("all.html", data=session["req-all"]))


@app.route("/fetch-token/configs/", methods=["POST"])
async def gen_conf():
    _data = await request.form
    data = _data["data"]
    rns = _data["rns"]
    if data != session["req-all"]:
        return "lol"
    session["req-all"] = (generate_id() + rns + generate_id())[:20]
    return Response(
        json.dumps({"id": session["req-all"], "rns": rns}),
        content_type="application/json",
    )


@app.route("/data/specs/", methods=["POST"])
async def get_all():
    json_data = {}
    _forms = await request.form
    forms = _forms["q"]
    json_data["movies"] = []
    if session["req-all"] != forms:
        return "!cool"
    movs = get_all_results(shuffle=True)
    json_data["movies"] = movs
    res = await make_response(json.dumps(json_data))
    res.headers["X-Sent-Cached"] = str(False)
    return res


@app.route("/fetch-token/links/post/", methods=["POST"])
async def s_confs():
    _data = await request.form
    data = _data["data"]
    if data != session["req-all"]:
        return "No"
    session["req-all"] = (generate_id() + generate_id())[:20]
    return Response(
        json.dumps({"id": session["req-all"]}), content_type="application/json"
    )


@app.route("/movie/<mid>/<mdata>/")
async def send_movie(mid, mdata):
    if mid is None:
        return "Nope"
    session["req_nonce"] = generate_id()
    if not os.path.isdir(".player-cache"):
        os.mkdir(".player-cache")
    if os.path.isfile(os.path.join(".player-cache", mid + ".json")):
        with open(os.path.join(".player-cache", mid + ".json"), "r") as f:
            try:
                data = json.loads(f.read())
                res = await make_response(
                    html_minify(
                        await render_template(
                            "player.html",
                            nonce=session["req_nonce"],
                            movie=data["movie_name"],
                            og_url=request.url,
                            og_image=data["thumbnail"],
                        )
                    )
                )
                res.headers["X-Sent-Cached"] = str(True)
                print("Sending Cached Data")
                return res
            except:
                pass
    meta_ = tvData.query.filter_by(mid=mid).first()
    if meta_ is None:
        return "No movie associated with given id"
    movie_name = meta_.moviedisplay
    thumbnail = meta_.thumb
    with open(os.path.join(".player-cache", mid + ".json"), "w") as f:
        data_js = {
            "movie_name": movie_name,
            "thumbnail": thumbnail,
            "episodes": meta_.episodes,
            "episode_meta": len(meta_.episodes),
            "season": meta_.season,
        }
        f.write(json.dumps(data_js))
    res = await make_response(
        html_minify(
            await render_template(
                "player.html",
                nonce=session["req_nonce"],
                movie=movie_name,
                og_url=request.url,
                og_image=thumbnail,
            )
        )
    )
    res.headers["X-Sent-Cached"] = str(False)
    return res


@app.route("/data-parser/plugins/player/", methods=["POST"])
async def plugin():
    _mid = await request.form
    mid = _mid["id"]
    if _mid["nonce"] != session["req_nonce"]:
        return "Lol"
    nonce = generate_id()
    session["req_nonce"] = nonce
    if os.path.isdir(".player-cache"):
        if os.path.isfile(os.path.join(".player-cache", mid + ".json")):
            with open(os.path.join(".player-cache", mid + ".json"), "r") as f:
                try:
                    data = json.loads(f.read())
                    json_data = {
                        "season": data["season"],
                        "episode_meta": data["episode_meta"],
                        "tempid": nonce,
                        "utf-8": "✓",
                        "movie_name": data["movie_name"],
                    }
                    res = await make_response(json.dumps(json_data))
                    res.headers["Content-Type"] = "application/json"
                    res.headers["X-Sent-Cached"] = str(True)
                    print("Sending Cached Data")
                    return res
                except:
                    pass
    else:
        os.mkdir(".player-cache")
    data = tvData.query.filter_by(mid=mid).first()
    common_ = {
        "season": data.season,
        "episode_meta": len(data.episodes),
        "movie_name": data.moviedisplay,
    }
    meta_data = {**common_, "episodes": data.episodes, "thumbnail": data.thumbnail}
    json_data = json.dumps({**common_, "tempid": nonce, "utf-8": "✓"})
    with open(os.path.join(".player-cache", mid + ".json"), "w") as f:
        f.write(json.dumps(meta_data))
    res = await make_response(json_data)
    res.headers["X-Sent-Cached"] = str(False)
    res.headers["Content-Type"] = "application/json"
    return res


@app.route("/build-player/ep/", methods=["POST"])
async def send_ep_data():
    eeid = await request.form
    eid = eeid["eid"]
    if eeid["nonce"] != session["req_nonce"]:
        return "LuL"
    episode = eeid["mid"]
    if os.path.isdir(".player-cache") and os.path.isfile(
        os.path.join(".player-cache", episode + ".json")
    ):
        with open(os.path.join(".player-cache", episode + ".json"), "r") as f:
            try:
                data = json.loads(f.read())
                episodes = data["episodes"]
                print("Cached Response")
                header = True
            except:
                pass
    else:
        header = False
        data = tvData.query.filter_by(mid=episode).first()
        episodes = data.episodes
    urls = episodes.get(int(eid)) or episodes.get(eid)
    json_data = {
        "url": str(urls[0]).replace("http:", "https:"),
        "alt1": str(urls[1]).replace("http:", "https:"),
        "alt2": str(urls[2]).replace("http:", "https:"),
    }
    res = await make_response(json.dumps(json_data))
    res.headers["Content-Type"] = "application/json"
    res.headers["X-Sent-Cached"] = str(header)
    return res


@app.route("/no-result/")
async def b404():
    return html_minify(await render_template("no-result.html"))


@app.route("/media/add/")
async def add_show():
    return await render_template("shows-add.html")


@app.route("/media/add-shows/fetch/")
async def search_shows():
    show = request.args.get("s")
    return Response(ippl_api.main_(term=show), content_type="application/json")


@app.websocket("/suggestqueries")
async def socket_conn():
    start_time = time.time()
    while 1:
        query = await websocket.receive()
        if (time.time() - start_time) >= 300:
            print("E")
            await websocket.send(
                json.dumps(
                    {
                        "data": [
                            {
                                "timeout": True,
                                "movie": "Please Refresh Your Browser..connection timed out",
                                "id": "_",
                                "thumbnail": "no",
                            }
                        ]
                    }
                )
            )
            return
        json_data = {"data": []}
        names = get_all_results(request_if_not_heroku=False)
        json_data["data"] = [
            s for s in names if re.search(r".*?%s" % (query), s["movie"], re.IGNORECASE)
        ]
        if len(json_data["data"]) == 0:
            await websocket.send(json.dumps({"no-res": True}))
        else:
            json_data["data"].sort(key=sort_dict)
            await websocket.send(json.dumps({**json_data, "cached": "undefined"}))


def sort_dict(el, key="movie"):
    return el.get(key)


@app.route("/add/tv-show/lookup")
async def add_show_lookup():
    _show_url = request.args.get("s")
    title = request.args.get("t", "")
    q = re.sub(r"([^\w]|_)", "", title).lower()
    urls = tvData.query.filter(tvData.movie.op("~")(r"(?s).*?%s" % (q))).all()
    if len(urls) > 0:
        return (
            "We already have a show with similar name..to prevent multiple copies of the same show..please request this show to be manually added",
            403,
        )
    thread = threading.Thread(target=ippl_api.get_, args=(_show_url, title))
    thread.start()
    return await render_template("shows_add_evt.html", show_url=_show_url, show=title)


@app.route("/sec/add/", methods=["POST"])
async def add_():
    try:
        _data = await request.form
        data = _data["lists"]
        if _data["pw"] != os.environ.get("_pass_"):
            return "No"
        data = json.loads(data)
        title = data["title"]
        thumb = data["thumb"]
        season = data["season"]
        episodes = data["episodes"]
        col = tvData(title, thumb, season, episodes)
        db.session.add(col)
        db.session.commit()
        print(col)
        return str(col)
    except Exception as e:
        print(e)
        return "Malformed Input" + str(e)


@app.route("/out")
async def redir():
    site = session.get("site-select")
    url = request.args.get("url")
    title = request.args.get("title", "TV Show")
    if url.startswith("//"):
        url = "https:" + url
    return await render_template("sites.html", url=url, site=site, title=title), 300


@app.route("/set-downloader/")
async def set_dl():
    session["site-select"] = request.args.get("dl")
    return redirect(session["site-select"], status_code=301)


@app.route("/admin/", methods=["POST", "GET"])
async def randomstuff():
    pw = app.secret_key
    if request.method == "GET":
        return html_minify(await render_template("admin.html"))
    else:
        if not is_heroku(request.url):
            print("Local")
            session["admin-auth"] = True
            resp = 1
        else:
            if session.get("admin-auth"):
                return Response(json.dumps({"response": -1}))
            form = await request.form
            _pass = form["pass"]
            session["admin-auth"] = _pass == pw
            if not session["admin-auth"]:
                resp = "0"
            else:
                resp = "1"
    return Response(json.dumps({"response": resp}), content_type="application/json")


@app.route("/admin/get-data/", methods=["POST"])
async def see_data():
    if not session.get("admin-auth"):
        return Response(json.dumps({}))
    _ = ("search", "moviewatch", "recommend", "movieclick")
    form = await request.form
    _type_ = form["type"].lower()
    _filter = [s.actions for s in DataLytics.query.filter_by(_type=_type_).all()]
    data = {"result": _filter}
    return Response(json.dumps(data), content_type="application/json")


@app.route("/collect/", methods=["POST", "GET"])
async def collect():
    if request.method == "POST":
        _data = await request.data
        data = json.loads(_data.decode())
    else:
        data = dict(request.args)
    if not is_heroku(request.url):
        print("Local Env")
        print(data)
        return ""
    col = DataLytics(data["type"].lower(), data["main"])
    db.session.add(col)
    db.session.commit()
    return ""


@app.route("/beacon-test", methods=["POST"])
async def bcontest():
    await request.data
    return ""


if __name__ == "__main__":
    app.run( host="0.0.0.0", port=5000, use_reloader=True)

