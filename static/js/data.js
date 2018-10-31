(function () {
    function urlencode(json, with_q) {
        return ((with_q) ? '?' : '') + Object.keys(json).map(function (key) {
            return encodeURIComponent(key) + '=' + encodeURIComponent(json[key]);
        }).join('&');
    };
    const hasBeaconSupport = (function (url = '/beacon-test', data = 'ok') {
        return navigator.sendBeacon(url, data);
    })();
    window.Beacon = {
        send: async function (url, data) {
            if (!hasBeaconSupport) {
                return (function () {
                    return (new Image()).src = url + urlencode(data, !!1);
                })()
            }
            if (typeof data === 'object') {
                data = JSON.stringify(data)
            }
            return navigator.sendBeacon(url, data);

        }
    };
})()