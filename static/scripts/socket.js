String.prototype.trunc = function (n) {
    return this.length > n ? `${this.substr(0, n - 1)}...` : this;
};
const dynamic_inp = document.getElementById("dynamic_inp");
const inp_res = document.getElementById('inp-results');

((() => {

    if (!window.WebSocket) {
        return;
    }
    const websocket_url = `${(window.location.protocol === 'https:' ? "wss://" : "ws://")}${window.location.host}/suggestqueries`;
    const ws = new WebSocket(websocket_url);
    dynamic_inp.oninput = function () {
        inp_res.innerHTML = "";
        make_req(this, ws);
    };
    ws.onopen = e => {
        console.log(e);
    };
    ws.onmessage = _msg_ => {
        inp_res.innerHTML = "";
        _msg = _msg_.data;
        inp_res.style.display = 'block';
        try {
            var msg = JSON.parse(_msg);
            if (msg['no-res']) {
                return;
            }
        } catch (e) {
            console.log(e);
            return;
        }
        const data = msg.data;
        console.log(`Response Cached:${msg.Cached}`);
        for (let i = 0; i < data.length; i++) {
            const js = data[i];
            const div = document.createElement("div");
            const span = document.createElement('span');
            div.setAttribute('data-im', js.id);
            div.onclick = function () {
                window.location = `/movie/${this.getAttribute('data-im')}/watch-suggested/`;
            };
            div.style.cursor = 'pointer';
            div.style.userSelect = 'none';
            div.style.listStyle = 'none';
            div.style.width = '45%';
            div.style.fontSize = 'small';
            div.className = 'sock-res';
            div.appendChild(span);
            div.style.margin = 'auto';
            span.innerHTML = js.movie;
            inp_res.appendChild(div);
            div.style.textAlign = 'left';
            div.style.border = '2px solid #e3e3e3';
            div.style.borderRadius = '5px';
        }
    };
}))();

window.onclick = e => {
    if (e.target.className !== 'input_n' && e.target.className !== 'sock-res' && e.target != inp_res) {
        inp_res.innerHTML = '';
    }
};

function make_req(e, ws) {
    const str = e.value;
    if (!check_inp(str)) {
        return;
    };
    ws.send(str);
}

function check_inp(str) {
    return str.replace(/([^\w]|_)/g, '').length !== 0;
}