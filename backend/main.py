from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp, os, uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

jobs = {}
history = []

# -------- GET VIDEO INFO --------

@app.get("/info")
def get_info(url: str):
    ydl_opts = {
        "quiet": True,
        "js_runtimes": {"node": {}}
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = []
    seen = set()

    for f in info.get("formats", []):
        fid = f.get("format_id")
        ext = f.get("ext")
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        note = f.get("format_note") or ""

        # VIDEO (has video codec)
        if fid and ext in ["mp4", "webm"] and vcodec != "none":
            key = (note, ext)
            if key in seen:
                continue
            seen.add(key)

            label = f"🎥 Video • {note} {ext.upper()}"
            formats.append({"id": fid, "label": label})

        # AUDIO ONLY (no video codec)
        if fid and vcodec == "none" and ext in ["m4a", "webm"]:
            abr = f.get("abr") or ""
            key = ("audio", abr, ext)
            if key in seen:
                continue
            seen.add(key)

            label = f"🎵 Audio • {abr} kbps {ext.upper()}"
            formats.append({"id": fid, "label": label})

   
    return {
        "title": info["title"],
        "thumbnail": info["thumbnail"],
        "formats": formats[:8]
    }

# -------- DOWNLOAD --------

@app.post("/download")
def download_video(url: str, format_id: str, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "downloading", "progress": 0}
    background_tasks.add_task(start_download, url, format_id, job_id)
    return {"job_id": job_id}

def start_download(url, format_id, job_id):
    try:
        def progress_hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                downloaded = d.get("downloaded_bytes", 0)
                jobs[job_id]["progress"] = int(downloaded/total*100)

        filename = f"{job_id}.mp4"

        ydl_opts = {
            "format": f"{format_id}+bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/{filename}",
            "progress_hooks": [progress_hook],
            "merge_output_format": "mp4",
            "quiet": True,
            "js_runtimes": {"node": {}}
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        jobs[job_id]["status"] = "done"
        jobs[job_id]["file"] = filename
        history.append(filename)

    except:
        jobs[job_id]["status"] = "error"

@app.get("/status/{job_id}")
def get_status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})

@app.get("/file/{filename}")
def get_file(filename: str):
    return FileResponse(os.path.join(DOWNLOAD_DIR, filename))

@app.get("/history")
def get_history():
    return history
