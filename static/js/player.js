const hash_episode = () => {
  hash_ep = window.location.hash.substr(1);
  if (hash_ep.length > 0) {
    reqs = parseqs(hash_ep);
    if (!isNaN(reqs.ep)) {
      console.log(reqs);
      get_url_for(reqs.ep, window.t_id);
      return;
    }
  }
  get_url_for(1, window.t_id);
};

function urlencode(json, with_q) {
  return (
    (with_q ? "?" : "") +
    Object.keys(json)
      .map(key => {
        return `${encodeURIComponent(key)}=${encodeURIComponent(json[key])}`;
      })
      .join("&")
  );
}
window.addEventListener("hashchange", () => {
  if (typeof window.t_id !== "undefined") {
    try {
      hash_episode();
    } catch (e) {
      console.log(e);
    }
  }
});
const parseqs = query => {
  const params = {};
  query = query[0] == "?" ? query.substring(1) : query;
  query = decodeURI(query);
  const vars = query.split("&");
  for (let i = 0; i < vars.length; i++) {
    const pair = vars[i].split("=");
    params[pair[0]] = decodeURIComponent(pair[1]);
  }
  return params;
};

const extractHostname = url => {
  try {
    let a;
    if (url.includes("://")) {
      a = new URL(url);
    } else {
      url = `http://${url}`;
      a = new URL(url);
    }
    return a.hostname;
  } catch (e) {
    return "null";
  }
};
const movie_id = window.location.pathname.split("/")[2];
const keys = "set-id";

function start_player(key) {
  console.log(key);
  //var params = eval('encodeURI("id=" + movie_id + "&nonce=" + nonce)');
  const params = urlencode(
    {
      id: movie_id,
      nonce
    },
    false
  );
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/dat" + "a-parser/" + "plugin" + "s/player/", true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

  xhr.onreadystatechange = () => {
    if (xhr.readyState == 4 && xhr.status == 200) {
      const data = xhr.response;
      set_meta_data(data);
    }
  };
  xhr.onerror = () => {
    const ifr = document.getElementById("player-frame");
    fetch("/error-configs/")
      .then(response => response.blob())
      .then(ret => {
        ifr.src = window.URL.createObjectURL(ret);
      });
  };
  xhr.send(params);
}

function set_meta_data(data) {
  data = JSON.parse(data);
  const episode_num = parseInt(data.episode_meta);
  window.movie_title = data.movie_name;
  window.t_id = data.tempid;
  for (let i = 0; i < episode_num; i++) {
    p = i + 1;
    const a = document.createElement("button"),
      link = document.createElement("a");
    a.innerText = `Episode ${p}`;
    a.setAttribute("data-eid", p);
    link.href = `#ep=${p}`;
    link.onclick = e => {
      e.preventDefault();
    };
    document.getElementById("ep_names").appendChild(link);
    link.appendChild(a);
    a.className = "episode-lists";
    a.onclick = function() {
      get_url_for(this.getAttribute("data-eid"), window.t_id);
      window.location.hash = `ep=${this.getAttribute("data-eid")}`;
    };
  }
  try {
    hash_episode();
    return;
  } catch (e) {
    console.log(e);
  }
  get_url_for(1, window.t_id);
}

const html_data =
  '<div style="margin-left:auto;margin-right:auto;text-align:center">Loading The Video</div>';
const __notif__ = new Blob([html_data], {
  type: "text/html"
});
const blobbed_notif = window.URL.createObjectURL(__notif__);

function get_url_for(eid, nonce) {
  const ifr = document.getElementById("player-frame");
  ifr.src = blobbed_notif;
  const req = new Request("/build-player/ep/", {
    method: "POST",
    body: urlencode(
      {
        eid,
        nonce,
        mid: movie_id
      },
      false
    ),
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    credentials: "include"
  });
  fetch(req)
    .then(res => res.text())
    .then(ret => {
      build_player(ret, "dummy-key-authorised", eid);
      document.getElementById(
        "curr-ep-id"
      ).innerHTML = `Now Playing-Episode ${eid}`;
      document.getElementById("download-episode-name").innerHTML = eid;
    })
    .catch(e => {
      console.error(e);
      fetch("/error-configs/")
        .then(response => response.blob())
        .then(ret => {
          ifr.src = window.URL.createObjectURL(ret);
        });
    });
}

function build_player(data, key, eid) {
  document.getElementById("custom-dl-box").style.display = "block";
  data = JSON.parse(data);
  const url = data["url"];
  const alt1 = data["alt1"];
  const alt2 = data["alt2"];
  const btns1 = document.getElementById("source1");
  const btns2 = document.getElementById("source2");
  const btns3 = document.getElementById("source3");
  const btndl1 = document.getElementById("dl-s1");
  const btndl2 = document.getElementById("dl-s2");
  const btndl3 = document.getElementById("dl-s3");
  const linkdl1 = document.getElementById("link-s1");
  const linkdl2 = document.getElementById("link-s2");
  const linkdl3 = document.getElementById("link-s3");

  function btndata(btn, btndl, url, linkdl, eid) {
    if (btn === null) {
      return;
    }
    if (url.includes("://")) {
      url = url.replace("http://", "https://");
    } else if (url.indexOf("//") == 0) {
      /* protocol relative url */
      url = `https:${url}`;
    }
    btn.setAttribute("data", url);
    btn.innerHTML = extractHostname(url);
    if (
      extractHostname(url) == "null" ||
      extractHostname(url).toLowerCase() == "none"
    ) {
      btn.style.display = "none";
      btndl.style.display = "none";
      linkdl.style.display = "none";
      return;
    } else {
      btn.style.display = "inline";
      btn.setAttribute("data", url.toString().replace("http://", "https://"));
      /* chrome will outright block any iframe in http */
    }
    btndl.style.display = btn.style.display;
    btndl.innerHTML = btn.innerHTML;
    linkdl.href = `/out${urlencode(
      {
        url,
        title: `${window.movie_title} episode:${eid}`
      },
      true
    )}`;
    btndl.innerHTML = btn.innerHTML;
    btn.onclick = function() {
      const ifr = document.getElementById("player-frame");
      document.getElementById("ifr-bx").removeChild(ifr);
      console.log(this.getAttribute("data"));
      Beacon.send("/collect/", {
        type: "moviewatch",
        main: {
          data: [
            {
              movie: document.querySelector('meta[name="movie"]').content,
              url: location.href
            }
          ],
          ua: navigator.userAgent,
          touch: navigator.maxTouchPoints > 0
        }
      });
      ifr.src = this.getAttribute("data");
      document.getElementById("ifr-bx").appendChild(ifr);
    };
  }
  btndata(btns1, btndl1, url, linkdl1, eid);
  btndata(btns2, btndl2, alt1, linkdl2, eid);
  btndata(btns3, btndl3, alt2, linkdl3, eid);
  const ifr = document.getElementById("player-frame");
  ifr.src = url;
}
document.getElementById("downloader-info").onclick = () => {
  document.getElementById("hdn-info").style.display = "block";
  document.getElementById("downloader-info").style.display = "none";
};
document.getElementById("d-linker").href = encodeURI(`/report?id=${movie_id}`);
document.getElementById("custom-dl").onclick = () => {
  document.getElementById("buttons-row").style.display = "block";
};
