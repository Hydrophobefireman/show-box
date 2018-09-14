var repo = document.getElementById("report-box");
const compat_url = window["URL"] || window["webkitURL"];
const req = new Request("{{thumb|safe}}");
const img = document.createElement("img");
img.style.height = '200px';
img.style.width = '150px;'
fetch(req)
    .then(response => response.blob())
    .then(blob => {
        img.src = compat_url.createObjectURL(blob);
    });
img.onload = function () {
    compat_url.revokeObjectURL(this.src)
}
repo.appendChild(img);
var repo = document.getElementById("report-box")
repo.appendChild(img);
const txtel = document.createElement("div");
txtel.innerHTML = "Report  movie {{title}}?"
repo.appendChild(txtel);

document.getElementById("sbmit-report").onclick = () => {
    const input_ = document.getElementById("episode-name");
    const reg = /^\d+$/;
    if (reg.test(input_.value)) {
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
    } else {
        alert("Invalid Episode Number")
    }
}