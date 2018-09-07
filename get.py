import base64
import json
import os
import random
import re
import secrets
import threading
import time
import uuid
from urllib.parse import quote, unquote

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
app.secret_key = ">%b3VAi&^{G"
dburl = os.environ.get("DATABASE_URL")
flaskUtils(app=app)
try:
    if dburl is None:
        with open(".dbinfo_", "r") as f:
            dburl = f.read().strip()
except FileNotFoundError:
    raise Exception(
        "No DB url specified try add it to the environment or create a \
        .dbinfo_ file with the url"
    )
app.config["SQLALCHEMY_DATABASE_URI"] = dburl
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/66.0.3343.3 Safari/537.36"


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
    if os.path.isfile(".db-cache--all"):
        with open(".db-cache--all", "r") as f:
            try:
                cached_data = json.loads(f.read())
                tst = cached_data.get("stamp")
                if time.time() - float(tst) < 600:
                    print("Sending Cached Data")
                    res = await make_response(json.dumps(cached_data.get("data")))
                    res.headers["X-Sent-Cached"] = str(True)
                    return res
            except json.decoder.JSONDecodeError:  # File manually emptied
                pass
    urls = tvData.query.all()
    random.shuffle(urls)
    for url in urls:
        json_data["movies"].append(
            {"movie": url.moviedisplay, "id": url.mid, "thumb": url.thumb}
        )
    if len(json_data["movies"]) == 0:
        return json.dumps({"no-res": True})
    meta_ = {"stamp": time.time(), "data": json_data}
    with open(".db-cache--all", "w") as fs:
        fs.write(json.dumps(meta_))
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
    common_ = {"season": data.season, "episode_meta": len(data.episodes)}
    meta_data = {
        **common_,
        "episodes": data.episodes,
        "movie_name": data.moviedisplay,
        "thumbnail": data.thumbnail,
    }
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
    while 1:
        query = await websocket.receive()
        file = ".db-cache--all"
        data = None
        json_data = {"data": []}
        no_data = True
        if os.path.isfile(file):
            no_data = False
            with open(file, "r") as f:
                _data = f.read()
            try:
                data = json.loads(_data)
                names = data["data"]["movies"]
                json_data["data"] = [
                    s
                    for s in names
                    if re.search(r".*?%s" % (query), s["movie"], re.IGNORECASE)
                ]
                await websocket.send(json.dumps({**json_data, "Cached": True}))
            except:
                no_data = True
        if no_data:
            urls = tvData.query.all()
            for url in urls:
                json_data["data"].append(
                    {"movie": url.moviedisplay, "id": url.mid, "thumb": url.thumb}
                )
            if len(json_data["data"]) == 0:
                return json.dumps({"no-res": True})
            meta_ = {"stamp": time.time(), "data": json_data}
            with open(file, "w") as fs:
                fs.write(json.dumps(meta_))
            await websocket.send(json.dumps({**json_data, "Cached": False}))


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
    if url.startswith("//"):
        url = "https:" + url
    return await render_template("sites.html", url=url, site=site), 300


@app.route("/set-downloader/")
async def set_dl():
    session["site-select"] = request.args.get("dl")
    return redirect(session["site-select"], status_code=301)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=True)

