const repo = document.getElementById("report-box");
const compat_url = window["URL"] || window["webkitURL"];
const req = new Request(document.querySelector("meta[name='og:image']").content);
const img = document.createElement("img");
img.style.height = '200px';
img.style.width = '150px;'
fetch(req)
    .then(response => response.blob())
    .then(blob => {
        img.src = compat_url.createObjectURL(blob);
    });
img.onload = self => {
    compat_url.revokeObjectURL(self.target.src)
}
repo.appendChild(img);

repo.appendChild(img);
const txtel = document.createElement("div");
txtel.innerHTML = `Report for movie ${window._title}`;
repo.appendChild(txtel);
document.getElementById("sbmit-report").onclick = () => {
    const report = new Request("/submit/report/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `id=${encodeURIComponent("{{m_id|safe}}")}`
    });
    fetch(report).then(response => response.text()).then(ret => {
        document.getElementById("sub-success-error").innerHTML = ret;
    })
}