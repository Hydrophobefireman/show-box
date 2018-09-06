String.prototype.trunc = function (n) {
    return (this.length > n) ? this.substr(0, n - 1) + '...' : this;
};
var dynamic_inp = document.getElementById("dynamic_inp");
var inp_res = document.getElementById('inp-results');

(() => {

    if (!window.WebSocket) {
        return;
    }
    var websocket_url = (window.location.protocol === 'https:' ? "wss://" : "ws://") + window.location.host + "/suggestqueries";
    var ws = new WebSocket(websocket_url);
    dynamic_inp.oninput = function () {
        inp_res.innerHTML = "";
        make_req(this, ws)
    };
    ws.onopen = function (e) {
        console.log(e)
    }
    ws.onmessage = function (_msg_) {
        _msg = _msg_.data;
        var msg = JSON.parse(_msg);
        var data = msg.data;
        console.log("Response Cached:" + msg.Cached);
        for (var i = 0; i < data.length; i++) {
            var js = data[i];
            var div = document.createElement("div");
            var span = document.createElement('span');
            var img = document.createElement('img');
            img.id = js.id;
            div.setAttribute('data-id', js.thumb);
            div.setAttribute('data-im', js.id)
            div.onclick = function () {
                window.location = '/movie/' + this.getAttribute('data-im') + "/movie"
            };
            div.style.cursor = 'pointer';
            div.style.listStyle = 'none';
            div.style.width = '80%';
            div.onmouseenter = function () {
                __img(document.getElementById(this.getAttribute('data-im')), this.getAttribute('data-id'))
            };
            document.ontouchstart = function () {
                __img(document.getElementById(this.getAttribute('data-im')), this.getAttribute('data-id'))
            }
            div.appendChild(img);
            div.appendChild(span);
            div.style.margin = 'auto';
            img.style.height = '80px';
            img.style.margin = '10px';
            span.innerHTML = js.movie;
            inp_res.appendChild(div);
            div.style.textAlign = 'left';
            div.style.border = '2px solid #e3e3e3';
            div.style.borderRadius = '5px';

        }
    };
})();

function make_req(e, ws) {
    var str = e.value;
    if (!check_inp(str)) {
        return;
    }
    ws.send(str);
}

function check_inp(str) {
    return str.replace(/([^\w]|_)/g, '').length !== 0;
}

function __img(img, imgURL) {
    if (img.src) {
        return
    }
    var compat_url = window["URL"] || window["webkitURL"];
    var req = new Request(imgURL);
    img.onload = function (self) {
        compat_url.revokeObjectURL(self.target.src);
    };
    fetch(req).then(function (response) {
        return response.blob();
    }).then(function (blob) {
        return compat_url.createObjectURL(blob);
    }).then(function (res) {
        img.src = res;
        img.style.backgroundColor = '';
    });
};