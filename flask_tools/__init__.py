import os
import uuid

from flask import (
    redirect,
    request,
    send_from_directory
)


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

        @app.after_request
        def after_req_headers(res):
            res.headers["X-Powered-By"] = "Flask"
            res.headers["X-UID"] = str(uuid.uuid4())
            return res

        @app.route("/favicon.ico")
        def send_fav():
            return send_from_directory(
                os.path.join(app.root_path, "static"),
                "favicon.ico",
                mimetype="image/x-icon")

        @app.before_request
        def https():
            if (app.config.get("FORCE_HTTPS_ON_PROD")
                    and request.endpoint in app.view_functions
                    and not request.is_secure
                    and "127.0.0.1" not in request.url
                    and "localhost" not in request.url):
                return redirect(
                    request.url.replace("http://", "https://"), code=301)
