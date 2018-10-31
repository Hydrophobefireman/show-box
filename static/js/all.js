const start = (params) => {
    const request = new Request("/dat" + "a/specs/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `q=${params}`,
        credentials: 'include'
    });
    fetch(request)
        .then(response => response.text())
        .then(response => {
            gen_results(response);
        }).catch(e => {
            nores_()
        })
}

const nores_ = () => {
    document.getElementById("main").style.display = 'none';
    document.getElementById("no-res").style.display = 'block';
};

const gen_results = (names) => {
    var names = JSON.parse(names);
    if (names.hasOwnProperty("no-res")) {
        nores_()
    };
    let i = 0;
    document.getElementById("skelly").style.display = 'none';
    for (; i < names["movies"]["length"]; i++) {
        const img = document.createElement("img");
        img.style.backgroundColor = '#e3e3e3';
        gen_img(img, names["movies"][i]["thumb"]);
        const dv = document.createElement("div");
        dv["className"] = "img-box";
        const atag = document.createElement("a");
        atag["href"] = encodeURI(`/movie/${names["movies"][i]["id"]}/${names["movies"][i]["movie"].replace(
    /(\(|\)|\s)/g, "-")}?id=${btoa(Math.random()).slice(0, 8)}`);
        atag.appendChild(img);
        dv.appendChild(atag);
        img.className = 'display-img';
        const sp = document.createElement("span");
        sp["className"] = "text-box";
        sp["innerHTML"] = names["movies"][i]["movie"];
        dv.appendChild(sp);
        document.getElementById("content").appendChild(dv);
    }
};
const gen_img = (img, imgURL) => {
    return new Promise((resolve, reject) => {
        const compat_url = window["URL"] || window["webkitURL"];
        const req = new Request(imgURL);
        img.onload = ({target}) => {
            compat_url.revokeObjectURL(target.src)
        };
        fetch(req)
            .then(response => response.blob())
            .then(blob => compat_url.createObjectURL(blob))
            .then(res => {
                img.src = res;
                img.style.backgroundColor = '';
                resolve(img);
            }).catch(e => {
                reject()
            });

    });
}

const fetch_2 = (data) => {
    const _params = `data=${encodeURIComponent(data)}`;
    const reqs = new Request('/fetch-token/links/post/', {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: _params,
        credentials: 'include'
    });
    fetch(reqs).then(ret => ret.json()).then(retcode => {
        data = retcode['id'];
        setTimeout(start(data), 700);
    })
};
((data) => {
    params = `data=${encodeURIComponent(data)}&rns=${btoa(Math.random().toString())}`;
    console.log(params)
    const reqs = new Request('/fetch-token/configs/', {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        credentials: 'include',
        body: params
    });
    fetch(reqs).then(ret => ret.json()).then(retcode => {
        data = retcode['id'];
        fetch_2(data);
    })
})(__data)