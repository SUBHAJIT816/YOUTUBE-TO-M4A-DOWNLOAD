import os
import tempfile
import shutil
import threading
from flask import Flask, request, send_file, render_template_string, jsonify
import yt_dlp

app = Flask(__name__)

# Global storage for progress tracking
download_progress = {}

# Modern UI with Glassmorphism, Progress Bar, and Enhanced UX
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamVault | Premium YT Downloader</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: radial-gradient(circle at top right, #1e1b4b, #000000); }
        .glass {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .loader-ring {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid #6366f1;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .progress-container {
            width: 100%;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 999px;
            overflow: hidden;
            height: 10px;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #22d3ee);
            width: 0%;
            transition: width 0.4s ease;
        }
    </style>
</head>
<body class="text-slate-200 min-h-screen flex items-center justify-center p-6">
    <div class="max-w-xl w-full">
        <!-- Header -->
        <div class="text-center mb-10">
            <h1 class="text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400 mb-2">
                StreamVault
            </h1>
            <p class="text-slate-400 text-lg">Download crystal clear audio in seconds</p>
        </div>

        <!-- Main Card -->
        <div class="glass rounded-3xl p-8 shadow-2xl relative overflow-hidden">
            <div class="relative z-10">
                <div class="space-y-6">
                    <div>
                        <label class="block text-sm font-semibold text-slate-400 mb-2 ml-1">YouTube URL</label>
                        <div class="flex flex-col sm:flex-row gap-3">
                            <input 
                                type="url" id="videoUrl" 
                                placeholder="Paste link here..." 
                                class="flex-1 bg-black/40 border border-white/10 rounded-2xl px-5 py-4 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all placeholder:text-slate-600"
                            >
                            <button 
                                onclick="analyzeVideo()" 
                                id="analyzeBtn"
                                class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-4 px-8 rounded-2xl transition-all shadow-lg shadow-indigo-500/20 active:scale-95 flex items-center justify-center min-w-[120px]"
                            >
                                <span id="analyzeText">Analyze</span>
                                <div id="analyzeLoader" class="loader-ring hidden"></div>
                            </button>
                        </div>
                    </div>

                    <!-- Video Preview Area -->
                    <div id="previewArea" class="hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div class="bg-black/20 rounded-2xl p-4 border border-white/5 flex flex-col gap-4">
                            <div class="flex gap-4 items-center">
                                <img id="videoThumb" src="" class="w-20 h-20 rounded-xl object-cover shadow-lg border border-white/10">
                                <div class="flex-1 min-w-0">
                                    <h3 id="videoTitle" class="font-bold text-white truncate text-base"></h3>
                                    <p id="videoDuration" class="text-slate-400 text-xs mt-1"></p>
                                    <button 
                                        onclick="startDownload()" 
                                        id="downloadActionBtn"
                                        class="mt-2 bg-white/5 hover:bg-white/10 border border-white/10 text-indigo-400 hover:text-indigo-300 px-4 py-2 rounded-lg font-bold text-xs transition-all flex items-center gap-2 group"
                                    >
                                        Confirm Download 
                                        <span class="group-hover:translate-x-1 transition-transform">→</span>
                                    </button>
                                </div>
                            </div>

                            <!-- Progress UI -->
                            <div id="progressUI" class="hidden space-y-2 mt-2 pt-4 border-t border-white/5">
                                <div class="flex justify-between text-xs font-semibold">
                                    <span id="progressStatus" class="text-slate-400 italic">Preparing...</span>
                                    <span id="progressPercent" class="text-indigo-400">0%</span>
                                </div>
                                <div class="progress-container">
                                    <div id="progressBar" class="progress-bar"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Status Messages -->
                    <div id="statusMsg" class="hidden text-center py-3 px-4 rounded-xl text-sm"></div>
                </div>
            </div>
        </div>

        <!-- Features Footer -->
        <div class="grid grid-cols-3 gap-4 mt-8">
            <div class="glass p-4 rounded-2xl text-center">
                <div class="text-indigo-400 mb-1">⚡</div>
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500">Fast</div>
            </div>
            <div class="glass p-4 rounded-2xl text-center">
                <div class="text-cyan-400 mb-1">🎧</div>
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500">M4A Format</div>
            </div>
            <div class="glass p-4 rounded-2xl text-center">
                <div class="text-rose-400 mb-1">🛡️</div>
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500">Secure</div>
            </div>
        </div>
    </div>

    <script>
        let currentTaskId = null;
        let progressInterval = null;

        async function analyzeVideo() {
            const url = document.getElementById('videoUrl').value;
            const btn = document.getElementById('analyzeBtn');
            const btnText = document.getElementById('analyzeText');
            const loader = document.getElementById('analyzeLoader');
            const preview = document.getElementById('previewArea');
            const status = document.getElementById('statusMsg');
            const progressUI = document.getElementById('progressUI');

            if (!url) return;

            status.classList.add('hidden');
            progressUI.classList.add('hidden');
            btn.disabled = true;
            btnText.classList.add('hidden');
            loader.classList.remove('hidden');

            try {
                const response = await fetch('/info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                
                const data = await response.json();
                if (data.error) throw new Error(data.error);

                document.getElementById('videoThumb').src = data.thumbnail;
                document.getElementById('videoTitle').innerText = data.title;
                document.getElementById('videoDuration').innerText = "Duration: " + data.duration;
                currentTaskId = data.task_id;
                
                preview.classList.remove('hidden');
                document.getElementById('downloadActionBtn').disabled = false;
                document.getElementById('downloadActionBtn').classList.remove('opacity-50');
            } catch (e) {
                status.innerText = "Error: " + e.message;
                status.classList.remove('hidden');
                status.classList.add('bg-rose-500/10', 'text-rose-400');
            } finally {
                btn.disabled = false;
                btnText.classList.remove('hidden');
                loader.classList.add('hidden');
            }
        }

        function startDownload() {
            const url = document.getElementById('videoUrl').value;
            const progressUI = document.getElementById('progressUI');
            const actionBtn = document.getElementById('downloadActionBtn');
            const statusText = document.getElementById('progressStatus');
            
            progressUI.classList.remove('hidden');
            actionBtn.disabled = true;
            actionBtn.classList.add('opacity-50');
            statusText.innerText = "Downloading...";

            if (progressInterval) clearInterval(progressInterval);
            progressInterval = setInterval(updateProgress, 1000);

            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/download';
            
            const inputUrl = document.createElement('input');
            inputUrl.type = 'hidden'; inputUrl.name = 'url'; inputUrl.value = url;
            form.appendChild(inputUrl);

            const inputId = document.createElement('input');
            inputId.type = 'hidden'; inputId.name = 'task_id'; inputId.value = currentTaskId;
            form.appendChild(inputId);
            
            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);
        }

        async function updateProgress() {
            if (!currentTaskId) return;

            try {
                const res = await fetch(`/progress/${currentTaskId}`);
                const data = await res.json();

                const bar = document.getElementById('progressBar');
                const text = document.getElementById('progressPercent');
                const statusText = document.getElementById('progressStatus');

                if (data.percent) {
                    const p = parseFloat(data.percent);
                    bar.style.width = p + '%';
                    text.innerText = Math.round(p) + '%';
                }

                if (data.status === 'finished') {
                    bar.style.width = '100%';
                    text.innerText = '100%';
                    statusText.innerText = 'Download Complete!';
                    clearInterval(progressInterval);
                }
            } catch (e) {
                console.error("Progress error", e);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({'error': 'No URL'}), 400

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            task_id = info.get('id', 'task_' + str(os.urandom(4).hex()))
            download_progress[task_id] = {'status': 'waiting', 'percent': '0'}
            
            return jsonify({
                'task_id': task_id,
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': f"{info.get('duration', 0) // 60}:{info.get('duration', 0) % 60:02d}"
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<task_id>')
def get_progress(task_id):
    progress = download_progress.get(task_id, {'status': 'not_found', 'percent': '0'})
    return jsonify(progress)

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form.get('url')
    task_id = request.form.get('task_id', 'unknown')
    
    if not video_url: return "URL is missing", 400

    # প্রগ্রেস হুক ফাংশনটি এখানে ডিফাইন করা হয়েছে যাতে এটি task_id এক্সেস করতে পারে
    def internal_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%', '').strip()
            download_progress[task_id] = {'status': 'downloading', 'percent': p}
        elif d['status'] == 'finished':
            download_progress[task_id] = {'status': 'finished', 'percent': '100'}

    temp_dir = tempfile.mkdtemp()
    try:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio', 
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'progress_hooks': [internal_hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)

            if os.path.exists(file_path):
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=os.path.basename(file_path)
                )
            else:
                return "Error generating file", 500

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    # threaded=True অত্যন্ত গুরুত্বপূর্ণ যাতে ডাউনলোড চলাকালীন প্রগ্রেস API কল করা যায়
    app.run(debug=True, port=5000, threaded=True)
