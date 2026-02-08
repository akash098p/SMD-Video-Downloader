const API = "http://127.0.0.1:8000";
let platform = "youtube";

/* ---------- THEME ---------- */
function toggleTheme(){
  document.body.classList.toggle("light");
}

/* ---------- INPUT CLEAR ---------- */
function toggleClear(){
  clearBtn.classList.toggle("show", url.value.length > 0);
}
function clearInput(){
  url.value="";
  toggleClear();
}

/* ---------- PLATFORM ---------- */
function setPlatform(p, btn){
  platform = p;
  document.querySelectorAll(".snackbar button")
    .forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  const placeholders={
    youtube:"Paste YouTube video URL",
    instagram:"Paste Instagram reel or post URL",
    facebook:"Paste Facebook video URL",
    x:"Paste X (Twitter) video URL"
  };

  document.getElementById("url").placeholder = placeholders[p];
}

/* ---------- TOAST ---------- */
function showToast(msg){
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

/* ---------- FETCH INFO ---------- */
async function fetchInfo(){
  if(!url.value.trim()){
    showToast("Paste a video URL");
    return;
  }

  info.innerHTML = `
    <div class="card">
      <div class="skeleton"></div>
      <div class="skeleton"></div>
      <div class="skeleton"></div>
    </div>
  `;

  const r = await fetch(`${API}/info?url=${encodeURIComponent(url.value)}`);
  const d = await r.json();

  let html = `
    <div class="card">
      <h3>${d.title}</h3>
      <img src="${d.thumbnail}" width="100%" style="border-radius:12px">
      <div class="grid">
  `;

  d.formats.forEach(f=>{
    html += `<button class="main" onclick="start('${f.id}')">${f.label}</button>`;
  });

  html += `</div></div>`;
  info.innerHTML = html;
}

/* ---------- START DOWNLOAD ---------- */
async function start(formatId){
  showToast("Download started");

  const r = await fetch(
    `${API}/download?url=${encodeURIComponent(url.value)}&format_id=${formatId}`,
    { method:"POST" }
  );
  const d = await r.json();
  createActiveJob(d.job_id);
}

/* ---------- JOB PROGRESS ---------- */
function createActiveJob(jobId){
  const div = document.createElement("div");
  div.className="card";
  div.innerHTML = `<div class="progress"><div></div></div>`;
  jobs.appendChild(div);

  const bar = div.querySelector(".progress div");

  const interval = setInterval(async()=>{
    const r = await fetch(`${API}/status/${jobId}`);
    const d = await r.json();

    bar.style.width = (d.progress || 0) + "%";

    if(d.status === "done"){
      clearInterval(interval);
      div.remove();
      addToHistory(d.file);
      showToast("Download completed");
    }
  },1000);
}

/* ---------- HISTORY ---------- */
function addToHistory(file){
  const div = document.createElement("div");
  div.className="card";
  div.innerHTML = `<a href="${API}/file/${file}" target="_blank">${file}</a>`;
  history.prepend(div);
}

async function loadHistory(){
  const r = await fetch(`${API}/history`);
  const h = await r.json();
  history.innerHTML="";
  h.forEach(addToHistory);
}

loadHistory();
