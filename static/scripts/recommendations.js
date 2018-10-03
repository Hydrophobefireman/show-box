(async () => {
    const gen_img = (img, imgURL) => {
        const host = window.location.hostname;
        if (host.includes('localhost') || window.location.host.includes('192.168') || !window.location
            .hostname
            .includes('herokuapp')) {
            img.style.backgroundColor = '#e3e3e3';
            return;
        }
        const compat_url = window["URL"] || window["webkitURL"];
        const req = new Request(imgURL);
        img.onload = ({
            target
        }) => {
            compat_url.revokeObjectURL(target.src)
        }
        fetch(req)
            .then(response => response.blob())
            .then(blob => compat_url.createObjectURL(blob))
            .then(res => {
                img.src = res;
                img.style.backgroundColor = '';
            });
    };
    const __data__ = await fetch('/i/rec/');
    const _data_ = await __data__.json();
    const data = _data_.recommendations;
    if (data.length === 0) {
        return
    }
    document.getElementById('recommend').style.display = 'flex';
    document.getElementById('rec-text').style.display = 'block';
    for (const b of data) {
        const movie = b.movie,
            id = b.id,
            sp = document.createElement("span");
        thumb = b.thumb;
        const div = document.createElement('div'),
            atag = document.createElement("span"),
            img = new Image()
        atag.appendChild(img);
        div.appendChild(atag);
        gen_img(img, thumb);
        div["className"] = "img-box";
        img.className = 'display-img';
        sp["className"] = "text-box";
        sp.innerText = movie;
        div.appendChild(sp);
        document.getElementById('r-content').appendChild(div);
        atag.onclick = e => {
            Beacon.send('/collect/', {
                type: 'recommend',
                main: {
                    ua: navigator.userAgent,
                    touch: (navigator.maxTouchPoints > 0),
                    data: [{
                        movie,
                        id
                    }]
                }
            })
            window.location = encodeURI(`/movie/${id}/${movie.replace(/[^\w]/g, "-")}`);
        }
    }
})()