import os
import uuid
import brotli
from flask import (redirect, request, send_from_directory)
config = {
    'COMPRESS_MIMETYPES': [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript'
    ],
    "COMPRESS_MIN_SIZE":
    500
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
        def https():
            request.process_time = time.time()
            if (app.config.get("FORCE_HTTPS_ON_PROD")
                    and request.endpoint in app.view_functions
                    and not request.is_secure
                    and "127.0.0.1" not in request.url
                    and "localhost" not in request.url):
                return redirect(
                    request.url.replace("http://", "https://"), code=307)

        @app.after_request
        def after_req_headers(res):
            res.headers['X-Process-Time'] = time.time() - request.process_time
            accept_encoding = request.headers.get('Accept-Encoding', '')
            res.headers["X-UID"] = str(uuid.uuid4())
            if (res.mimetype not in config['COMPRESS_MIMETYPES']
                    or 'br' not in accept_encoding.lower()
                    or not 200 <= res.status_code < 300
                    or (res.content_length is not None
                        and res.content_length < config['COMPRESS_MIN_SIZE'])
                    or 'Content-Encoding' in res.headers):
                return res
            res.direct_passthrough = False
            uncompressed_length = res.content_length
            res.set_data(brotli_content(res))
            res.headers['Content-Encoding'] = 'br'
            res.headers['Content-Length'] = res.content_length
            res.headers['X-Compression-Percentage'] = int(
                (res.content_length / uncompressed_length) * 100)
            vary = res.headers.get('Vary')
            if vary:
                if 'accept-encoding' not in vary.lower():
                    res.headers['Vary'] = '%s, Accept-Encoding' % (vary)
            else:
                res.headers['Vary'] = 'Accept-Encoding'

            return res

        @app.route("/favicon.ico")
        def send_fav():
            return send_from_directory(
                os.path.join(app.root_path, "static"),
                "favicon.ico",
                mimetype="image/x-icon")


def brotli_content(response):
    data = response.get_data()
    deflated = brotli.compress(data)
    return deflated
