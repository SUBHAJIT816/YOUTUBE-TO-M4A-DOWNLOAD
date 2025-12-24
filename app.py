from flask import Flask, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube to M4A</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body{
            margin:0;
            height:100vh;
            display:flex;
            justify-content:center;
            align-items:center;
            background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);
            font-family:Arial, sans-serif;
        }
        .box{
            background:#111;
            padding:35px;
            width:320px;
            border-radius:14px;
            text-align:center;
            box-shadow:0 25px 50px rgba(0,0,0,.6);
        }
        h1{
            color:#00c6ff;
            margin-bottom:10px;
        }
        p{
            color:#aaa;
            font-size:14px;
        }
        input{
            width:100%;
            padding:12px;
            margin-top:15px;
            border-radius:8px;
            border:none;
            outline:none;
        }
        button{
            width:100%;
            padding:12px;
            margin-top:15px;
            border:none;
            border-radius:8px;
            background:#00c6ff;
            font-size:16px;
            cursor:pointer;
        }
        button:hover{
            background:#0072ff;
            color:white;
        }
        footer{
            margin-top:15px;
            font-size:11px;
            color:#666;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>YouTube → M4A</h1>
        <p>Fast & Smooth Audio Downloader</p>
        <form method="POST">
            <input type="url" name="url" placeholder="Paste YouTube link" required>
            <button type="submit">Download M4A</button>
        </form>
        <footer>Educational purpose only</footer>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form["url"]
        filename = str(uuid.uuid4())
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": filepath,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }],
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(filepath + ".m4a", as_attachment=True)

    return HTML_PAGE

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
