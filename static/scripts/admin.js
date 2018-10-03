(() => {
    const $ = document.querySelector.bind(document),
        btn = $('#go'),
        $content = $("#content"),
        $jsonres = $("#json-res"),
        inp = $("#postit");

    const $getdata = async (act) => {
        $jsonres.innerHTML = 'Fetching Results';
        const _res = await fetch('/admin/get-data/', {
            method: "POST",
            body: `type=${encodeURIComponent(act)}`,
            headers: {
                'content-type': 'application/x-www-form-urlencoded'
            }
        });
        const data = await _res.json();
        const res = data.result;
        $jsonres.innerHTML = '';
        for (var b of res) {
            var pre = document.createElement('pre');
            pre.innerHTML = JSON.stringify(b, null, 3);
            $jsonres.appendChild(pre);
            pre.style.border = '2px solid';
        }
    }

    function paint_page() {
        $content.innerHTML = '';
        _types = ['search', 'moviewatch', 'recommend', 'movieclick'];
        const _disc = document.createElement('div');
        for (const b of _types) {
            const sbtn = document.createElement('button');
            sbtn.innerHTML = b;
            _disc.appendChild(sbtn);
            sbtn.dataset.action = b;
            sbtn.className = 'aval-type';
            sbtn.onclick = function () {
                $getdata(this.dataset.action)
            };
        }
        $content.appendChild(_disc);
    }
    btn.onclick = async () => {
        const __data = await fetch('/admin/', {
            method: 'POST',
            body: `pass=${inp.value.trim()}`,
            headers: {
                'content-type': 'application/x-www-form-urlencoded'
            }
        });
        const _resp = await __data.json();
        const resp = _resp.response;
        if (resp === 1 || resp === -1) {
            btn.remove();
            inp.remove();
            paint_page()
        } else {
            return
        }
    }
})()