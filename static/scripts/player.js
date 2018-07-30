function parseqs(query) {
    var params = {};
    query = ((query[0] == '?') ? query.substring(1) : query);
    query = decodeURI(query);
    var vars = query.split('&');
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split('=');
        params[pair[0]] = pair[1];
    }
    return params;
}

function extractHostname(url) {
    try {
        var a;
        if (url.indexOf("://") > -1) {
            a = new URL(url);

        } else {
            url = "http://" + url;
            a = new URL(url);
        }
        return a.hostname;
    } catch (e) {
        return 'null'
    }
}
var movie_id = window.location.pathname.split("/")[2]
var keys = "set-id"

function start_player(key) {
    console.log(key);
    var params = eval('encodeURI("id=" + movie_id + "&nonce=" + nonce)');
    var xhr = new XMLHttpRequest();
    xhr.open("POST", '/dat' + 'a-parser/' + 'plugin' + 's/player/', true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var data = xhr.response;
            set_meta_data(data);
        }
    }
    xhr.onerror = function () {
        var ifr = document.getElementById("player-frame");
        fetch("/error-configs/")
            .then(response => response.blob()).then(ret => {
                ifr.src = window.URL.createObjectURL(ret);
            })
    }
    xhr.send(params);
}

function set_meta_data(data) {
    data = JSON.parse(data);
    var episode_num = parseInt(data.episode_meta);
    var t_id = data.tempid;
    for (var i = 0; i < episode_num; i++) {
        p = i + 1;
        var a = document.createElement("button");
        a.innerText = "Episode " + p;
        a.setAttribute("data-eid", p);
        document.getElementById("ep_names").appendChild(a);
        a.className = "episode-lists";
        a.onclick = function () {
            get_url_for(this.getAttribute('data-eid'), t_id);
        }
    }
    try {
        hash_ep = window.location.hash.substr(1);
        if (hash_ep.length > 0) {
            reqs = parseqs(hash_ep);
            if (!isNaN(reqs.ep)) {
                console.log(reqs)
                get_url_for(reqs.ep, t_id);
                return
            }
        }
        get_url_for("1", t_id)
    } catch (e) {
        console.log(e);
    }
}

var html_data =
    '<div style="margin-left:auto;margin-right:auto;text-align:center">Loading The Video</div>';
var __notif__ = new Blob([html_data], {
    type: "text/html"
});
var blobbed_notif = window.URL.createObjectURL(__notif__);

function get_url_for(eid, nonce) {
    var ifr = document.getElementById("player-frame");
    ifr.src = blobbed_notif;
    var req = new Request("/build-player/ep/", {
        method: "POST",
        body: "eid=" + encodeURIComponent(eid) + "&nonce=" + encodeURIComponent(nonce) + "&mid=" +
            encodeURIComponent(movie_id),
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        credentials: "include"
    });
    fetch(req)
        .then(res => res.text()).then(ret => {
            build_player(ret, "dummy-key-authorised")
            document.getElementById("curr-ep-id").innerHTML = "Now Playing-Episode " + eid;
            document.getElementById("download-episode-name").innerHTML = eid;
        }).catch(e => {
            console.error(e);
            fetch("/error-configs/")
                .then(response => response.blob()).then(ret => {
                    ifr.src = window.URL.createObjectURL(ret);
                });
        });
}


function build_player(data, key) {
    document.getElementById("custom-dl-box").style.display = 'block';
    data = JSON.parse(data);
    var url = data['url'];
    var alt1 = data['alt1'];
    var alt2 = data['alt2'];
    var btns1 = document.getElementById("source1");
    var btns2 = document.getElementById("source2");
    var btns3 = document.getElementById("source3");
    var btndl1 = document.getElementById("dl-s1");
    var btndl2 = document.getElementById("dl-s2");
    var btndl3 = document.getElementById("dl-s3");
    var linkdl1 = document.getElementById("link-s1");
    var linkdl2 = document.getElementById("link-s2");
    var linkdl3 = document.getElementById("link-s3");

    function btndata(btn, btndl, url, linkdl) {
        if (url.indexOf("://") > -1) {
            url = url.replace("http://", "https://");

        } else if (url.indexOf("//") == 0) {
            /* protocol relative url */
            url = "https:" + url;
        }
        btn.setAttribute("data", url);
        btn.innerHTML = extractHostname(url);
        if (extractHostname(url) == "null" || extractHostname(url).toLowerCase() == 'none') {
            btn.style.display = 'none'
        } else {
            btn.style.display = 'inline';
            btn.setAttribute('data', url.toString().replace("http://", "https://"));
            /* chrome will outright block any iframe in http */
        }
        btndl.style.display = btn.style.display;
        btndl.innerHTML = btn.innerHTML;
        linkdl.href = "/out?url=" + encodeURIComponent(url);
        btndl.innerHTML = btn.innerHTML;
        btn.onclick = function () {
            var ifr = document.getElementById("player-frame");
            document.getElementById("ifr-bx").removeChild(ifr);
            ifr.src = this.getAttribute("data");
            document.getElementById("ifr-bx").appendChild(ifr);
        }
    }
    btndata(btns1, btndl1, url, linkdl1);
    btndata(btns2, btndl2, alt1, linkdl2);
    btndata(btns3, btndl3, alt2, linkdl3);
    var ifr = document.getElementById("player-frame");
    ifr.src = url;
}
document.getElementById("downloader-info").onclick = function () {
    document.getElementById("hdn-info").style.display = 'block';
    document.getElementById("downloader-info").style.display = 'none';
}

document.getElementById("d-linker").onclick = function () {
    window.location = encodeURI("/report?id=" + movie_id);
};
document.getElementById("custom-dl").onclick = function () {
    document.getElementById("buttons-row").style.display = 'block';
}