import os
import uuid
import brotli
from flask import redirect, request, send_from_directory

config = {
    "COMPRESS_MIMETYPES": [
        "text/html",
        "text/css",
        "text/xml",
        "application/json",
        "application/javascript",
    ],
    "COMPRESS_MIN_SIZE": 500,
}

import time


class flaskUtils(object):
    def __init__(self, app=None):
        self.app = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if "utils_ext" in app.extensions:
            raise RuntimeError("utils extension already initialized")
        app.extensions["utils_ext"] = self
        self.app = app

        @app.before_request
        def enforce_https():
            request.process_time = time.time()
            if (
                request.endpoint in app.view_functions
                and not request.is_secure
                and not "127.0.0.1" in request.url
                and not "localhost" in request.url
                and not "192.168." in request.url
                and request.url.startswith("http://")
            ):
                rd = request.url.replace("http://", "https://")
                if "?" in rd:
                    rd += "&rd=ssl"
                else:
                    rd += "?rd=ssl"
                return redirect(rd, code=307)

        @app.after_request
        def after_req_headers(res):
            res.headers["X-Process-Time"] = time.time() - request.process_time
            accept_encoding = request.headers.get("Accept-Encoding", "")
            res.headers["X-UID"] = str(uuid.uuid4())
            return res

        @app.route("/favicon.ico")
        def send_fav():
            return send_from_directory(
                os.path.join(app.root_path, "static"),
                "favicon.ico",
                mimetype="image/x-icon",
            )


def brotli_content(response):
    data = response.get_data()
    deflated = brotli.compress(data)
    return deflated
