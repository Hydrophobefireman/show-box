import base64
import json
import os
import random
import re
import time
import uuid
from urllib.parse import quote, unquote

import psycopg2
import requests
from bs4 import BeautifulSoup as bs
from flask import (Flask, redirect, render_template, request, Response,
                   send_from_directory, session, url_for, make_response)
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy
from htmlmin.minify import html_minify
from jac.contrib.flask import JAC

import streamsites as st
from dbmanage import req_db

app = Flask(__name__)
Compress(app)
app.config['COMPRESSOR_DEBUG'] = app.config.get('DEBUG')
app.config['COMPRESSOR_OUTPUT_DIR'] = './static/jsbin'
app.config['COMPRESSOR_STATIC_PREFIX'] = '/static/jsbin/'
jac = JAC(app)
app.secret_key = "H(|hGh<;e"
dburl = os.environ.get('DATABASE_URL')

try:
    if dburl is None:
        with open(".dbinfo_", "r") as f:
            dburl = f.read().strip()
except FileNotFoundError:
    raise Exception(
        "No DB url specified try add it to the environment or create a .dbinfo_ file with the url")
app.config['SQLALCHEMY_DATABASE_URI'] = dburl
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3343.3 Safari/537.36"


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
        self.movie = re.sub(r"\s", "", movie.lower())
        self.moviedisplay = movie
        self.thumb = thumb

    def __repr__(self):
        return '<Name %r>' % self.movie


def generate_id():
    lst_ = list(base64.urlsafe_b64encode((str(uuid.uuid1())+str(uuid.uuid4()) +
                                          uuid.uuid4().hex+str(time.time())).encode()).decode().replace("=", '--'))
    random.shuffle(lst_)
    return ''.join(lst_)[:gen_rn()]


def gen_rn():
    return random.randint(5, 17)


class tvRequests(db.Model):
    r_id = db.Column(db.Integer, primary_key=True)
    movie = db.Column(db.String(100))
    url = db.Column(db.String(1000))

    def __init__(self, movie, url=None):
        self.movie = movie
        self.url = url

    def __repr__(self):
        return '<Name %r>' % self.movie


class deadLinks(db.Model):
    r_id = db.Column(db.Integer, primary_key=True)
    movieid = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    def __init__(self, movie_id, name=None):
        self.movieid = movie_id
        self.name = name

    def __repr__(self):
        return '<Name %r>' % self.movieid


@app.before_request
def https():
    if request.endpoint in app.view_functions and not request.is_secure and "127.0.0.1" not in request.url and not "localhost" in request.url:
        return redirect(request.url.replace("http://", "https://"), code=301)


@app.route("/robots.txt")
def check__():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'robots.txt', mimetype='text/plain')


@app.route("/")
def index():
    if session.get("req-data"):
        d = "Thanks for helping us out!"
    else:
        d = " "
    return html_minify(render_template("index.html", msg=d))


@app.route("/report/")
def report_dead():
    m_id = request.args.get("id")
    if m_id is None:
        return "No movie id specified"
    meta_ = tvData.query.filter_by(mid=m_id).first()
    if meta_ is None:
        return "No movie associated with given id"
    thumb = meta_.thumb
    title = meta_.moviedisplay
    return render_template("link-report.html", m_id=m_id, title=title, thumb=thumb)


@app.route("/submit/report/", methods=['POST'])
def parse_report():
    try:
        mid = request.form['id']
        col = deadLinks(mid)
        db.session.add(col)
        db.session.commit()
        return "Response recorded.Thank You for your help!"
    except Exception as e:
        print(e)
        return "An unknown error occured during processing your request"
       # raise e


@app.route("/search")
def send_m():
    if request.args.get("q") is None or not re.sub(r"[^\w]", "", request.args.get("q")):
        return "Specify a term!"
    return html_minify(render_template("movies.html", q=request.args.get("q")))


@app.route("/help-us/")
def ask_get():
    return html_minify(render_template("help.html"))


@app.route("/db-manage/parse-requests/", methods=['POST'])
def get_s():
    movie = request.form.get('movie')
    if not re.sub(r"\s", "", movie):
        print("No movie Given")
        return "Please mention the movie"
    url = request.form.get('url')
    data = (movie, url)
    a = req_db(data)
    print(a)
    return redirect("/", 301)


@app.route("/googlef06ee521abc7bdf8.html")
def google_():
    return "google-site-verification: googlef06ee521abc7bdf8.html"


@app.route("/data/search/", methods=['POST'])
def serchs():
    json_data = {}
    json_data['movies'] = []
    q = re.sub(r"\s", "", request.form["q"]).lower()
    urls = tvData.query.filter(
        tvData.movie.op("~")(r"(?s).*?%s" % (q))).all()
    for url in urls:
        json_data['movies'].append(
            {"movie": url.moviedisplay, 'id': url.mid, "thumb": url.thumb})
    if len(json_data['movies']) == 0:
        return json.dumps({'no-res': True})
    return json.dumps(json_data)


@app.route("/error-configs/")
def err_configs():
    return render_template("err.html")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/x-icon')


@app.route("/all/", strict_slashes=False)
def all_movies():
    session['req-all'] = (generate_id()+generate_id())[:20]
    return html_minify(render_template("all.html", data=session['req-all']))


@app.route("/fetch-token/configs/", methods=['POST'])
def gen_conf():
    data = request.form['data']
    rns = request.form['rns']
    if data != session['req-all']:
        return 'lol'
    session['req-all'] = (generate_id()+rns+generate_id())[:20]
    return Response(json.dumps(
        {"id": session['req-all'], "rns": rns}), content_type='application/json')


@app.route("/data/specs/", methods=['POST'])
def get_all():
    json_data = {}
    forms = request.form['q']
    json_data['movies'] = []

    if session['req-all'] != forms:
        return "!cool"
    urls = tvData.query.all()
    random.shuffle(urls)
    for url in urls:
        json_data['movies'].append(
            {"movie": url.moviedisplay, 'id': url.mid, "thumb": url.thumb})
    if len(json_data['movies']) == 0:
        return json.dumps({'no-res': True})
    return json.dumps(json_data)


@app.route('/fetch-token/links/post/', methods=['POST'])
def s_confs():
    data = request.form['data']
    if data != session['req-all']:
        return "No"
    session['req-all'] = (generate_id()+generate_id())[:20]
    return Response(json.dumps(
        {"id": session['req-all']}), content_type='application/json')


@app.route("/movie/<mid>/<mdata>/")
def send_movie(mid, mdata):
    if mid is None:
        return "Nope"
    meta_ = tvData.query.filter_by(mid=mid).first()
    if meta_ is None:
        return "No movie associated with given id"
    movie_name = meta_.moviedisplay
    thumbnail = meta_.thumb
    r_n = random.randint(4, 25)
    session['req_nonce'] = (str(uuid.uuid1())+str(uuid.uuid4()))[:r_n]
    return html_minify(render_template("player.html", nonce=session['req_nonce'], movie=movie_name, og_url=request.url, og_image=thumbnail))


@app.route("/data-parser/plugins/player/", methods=['POST'])
def plugin():
    mid = request.form['id']
    if request.form['nonce'] != session['req_nonce']:
        return "Lol"
    nonce = generate_id()
    session['req_nonce'] = nonce
    data = tvData.query.filter_by(mid=mid).first()
    json_data = {"season": data.season, "episode_meta": len(
        data.episodes), "tempid": nonce, "utf-8": "✓"}
    return json.dumps(json_data)


@app.route("/build-player/ep/", methods=['POST'])
def send_ep_data():
    eid = request.form['eid']
    if request.form['nonce'] != session['req_nonce']:
        return "Lol"
    episode = request.form['mid']
    data = tvData.query.filter_by(mid=episode).first()
    episodes = data.episodes
    urls = episodes[int(eid)]
    json_data = {"url": str(urls[0]).replace("http:", "https:"), 'alt1': str(
        urls[1]).replace("http:", "https:"), 'alt2': str(urls[2]).replace("http:", "https:")}
    return json.dumps(json_data)


@app.route("/no-result/")
def b404():
    return html_minify(render_template("no-result.html"))


@app.route("/pw/add/", methods=['POST'])
def abckdv():
    data = request.form['u']
    pass_ = request.form["p"]
    req_db((data, pass_))
    return "die"


@app.route("/sec/add/", methods=['POST'])
def add_():
    try:
        data = request.form['lists']
        if request.form['pw'] != os.environ.get("_pass_"):
            return "No"
        data = json.loads(data)
        title = data['title']
        thumb = data['thumb']
        season = data['season']
        episodes = json.loads(data['episodes'])
        col = tvData(title, thumb, season, episodes)
        db.session.add(col)
        db.session.commit()
        print(col)
        return str(col)
    except Exception as e:
        print(e)
        return "Malformed Input"+str(e)


@app.route("/out")
def redir():
    url = request.args.get("url")
    return redirect("https://dl-js.herokuapp.com/video?url="+quote(url))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
