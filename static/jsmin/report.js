var repo=document.getElementById("report-box");const compat_url=window.URL||window.webkitURL,req=new Request("{{thumb|safe}}"),img=document.createElement("img");img.style.height="200px",img.style.width="150px;",fetch(req).then(e=>e.blob()).then(e=>{img.src=compat_url.createObjectURL(e)}),img.onload=function(){compat_url.revokeObjectURL(this.src)},repo.appendChild(img),(repo=document.getElementById("report-box")).appendChild(img);const txtel=document.createElement("div");txtel.innerHTML="Report  movie {{title}}?",repo.appendChild(txtel),document.getElementById("sbmit-report").onclick=(()=>{const e=document.getElementById("episode-name");if(/^\d+$/.test(e.value)){const e=new Request("/submit/report/",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"id="+encodeURIComponent("{{m_id|safe}}")});fetch(e).then(e=>e.text()).then(e=>{document.getElementById("sub-success-error").innerHTML=e})}else alert("Invalid Episode Number")});