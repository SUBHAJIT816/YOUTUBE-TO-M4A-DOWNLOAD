from flask import Flask, render_template_string, request, send_file, jsonify
import io
import re
import json
import urllib.request
import urllib.error
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

app = Flask(__name__)

# --- Configuration ---
apiKey = "" 

# --- UI Templates (Tailwind CSS based with RED TIGER Branding) ---
NAV_HTML = """
<nav class="bg-white border-b border-gray-200 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
            <div class="flex items-center gap-2">
                <span class="text-2xl text-red-600 font-bold">🐅</span>
                <span class="text-xl font-black tracking-tighter bg-gradient-to-r from-red-600 via-orange-500 to-black bg-clip-text text-transparent">
                    RED TIGER WORKSPACE
                </span>
            </div>
            <div class="flex items-center gap-6">
                <a href="/" class="text-sm font-medium text-gray-600 hover:text-red-600 transition">Dashboard</a>
                <a href="/word" class="text-sm font-medium text-gray-600 hover:text-red-600 transition">Word</a>
                <a href="/sheet" class="text-sm font-medium text-gray-600 hover:text-red-600 transition">Sheet</a>
            </div>
        </div>
    </div>
</nav>
"""

# ---------------- API ROUTES ----------------

@app.route("/api/ai", methods=["POST"])
def ai_assistant():
    """Gemini AI Assistant using built-in urllib"""
    data = request.json
    prompt = data.get("prompt", "")
    content = data.get("content", "")
    full_prompt = f"{prompt}: \n\n {content}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={apiKey}"
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "systemInstruction": {"parts": [{"text": "You are a professional writing assistant for RED TIGER WORKSPACE. Provide sharp, accurate, and creative edits."}]}
    }
    
    try:
        req = urllib.request.Request(url, method="POST")
        req.add_header('Content-Type', 'application/json')
        body = json.dumps(payload).encode('utf-8')
        with urllib.request.urlopen(req, data=body) as response:
            result = json.loads(response.read().decode('utf-8'))
        text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No response from AI.')
        return jsonify({"result": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- PAGE ROUTES ----------------

@app.route("/")
def home():
    return render_template_string(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RED TIGER WORKSPACE - Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Inter', sans-serif; background: #fafafa; }}</style>
</head>
<body>
    {NAV_HTML}
    <main class="max-w-7xl mx-auto px-4 py-16">
        <div class="text-center mb-16">
            <h1 class="text-5xl font-black text-gray-900 mb-4 tracking-tight">RED TIGER <span class="text-red-600">OFFICE</span></h1>
            <p class="text-lg text-gray-500 max-w-2xl mx-auto">Ultimate power workspace for the modern professional. Create, calculate, and innovate with AI.</p>
        </div>
        
        <div class="grid md:grid-cols-2 gap-10 max-w-4xl mx-auto">
            <div class="bg-white p-10 rounded-3xl shadow-sm border border-gray-100 hover:border-red-200 transition-all group">
                <div class="w-16 h-16 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center mb-6 text-3xl group-hover:scale-110 transition">📝</div>
                <h3 class="text-2xl font-bold mb-2">Tiger Word</h3>
                <p class="text-gray-500 mb-8">AI-powered editor with professional formatting and export features.</p>
                <a href="/word" class="block text-center bg-gray-900 text-white px-8 py-4 rounded-2xl font-bold hover:bg-red-600 transition shadow-lg shadow-gray-200">Launch Editor</a>
            </div>

            <div class="bg-white p-10 rounded-3xl shadow-sm border border-gray-100 hover:border-red-200 transition-all group">
                <div class="w-16 h-16 bg-orange-50 text-orange-600 rounded-2xl flex items-center justify-center mb-6 text-3xl group-hover:scale-110 transition">📊</div>
                <h3 class="text-2xl font-bold mb-2">Tiger Sheet</h3>
                <p class="text-gray-500 mb-8">Fast, reactive spreadsheet for complex data and analytics.</p>
                <a href="/sheet" class="block text-center bg-gray-900 text-white px-8 py-4 rounded-2xl font-bold hover:bg-red-600 transition shadow-lg shadow-gray-200">Launch Sheet</a>
            </div>
        </div>
    </main>
</body>
</html>
""")

@app.route("/word")
def word():
    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Tiger Word - RED TIGER</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        #editor {{ min-height: 297mm; width: 210mm; }}
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    {NAV_HTML}
    
    <div class="bg-white border-b border-gray-200 py-3 sticky top-16 z-40 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 flex gap-4 items-center flex-wrap">
            <div class="flex bg-gray-50 p-1.5 rounded-xl border border-gray-100">
                <button onclick="cmd('bold')" class="px-3 py-1 hover:bg-white rounded-lg transition font-bold">B</button>
                <button onclick="cmd('italic')" class="px-3 py-1 hover:bg-white rounded-lg transition italic">I</button>
                <button onclick="cmd('underline')" class="px-3 py-1 hover:bg-white rounded-lg transition underline">U</button>
            </div>
            
            <div class="flex items-center gap-2 bg-gray-50 p-1.5 rounded-xl border border-gray-100">
                <label class="text-[10px] uppercase font-bold text-gray-400 ml-1">Color</label>
                <input type="color" onchange="cmd('foreColor', this.value)" class="w-7 h-7 p-0 border-none cursor-pointer bg-transparent">
            </div>

            <select onchange="cmd('fontSize', this.value)" class="border border-gray-100 bg-gray-50 rounded-xl px-3 py-1.5 outline-none text-sm font-medium">
                <option value="3">Small</option><option value="4" selected>Normal</option>
                <option value="5">Large</option><option value="6">Heading</option>
            </select>

            <div class="h-6 w-px bg-gray-200"></div>

            <button onclick="askAI('Rewrite this text professionally')" class="bg-red-50 text-red-700 px-4 py-1.5 rounded-xl border border-red-100 text-sm font-bold hover:bg-red-100 transition flex items-center gap-2">✨ Rewrite</button>
            <button onclick="askAI('Summarize this text into bullet points')" class="bg-gray-50 text-gray-700 px-4 py-1.5 rounded-xl border border-gray-100 text-sm font-bold hover:bg-gray-200 transition">📝 Summary</button>

            <div class="flex-grow"></div>
            <button onclick="exportPDF()" class="bg-red-600 text-white px-6 py-2 rounded-xl hover:bg-red-700 shadow-md shadow-red-100 text-sm font-bold transition">Export PDF</button>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 py-12 flex justify-center">
        <div id="editor" contenteditable="true" class="bg-white shadow-2xl p-24 outline-none leading-relaxed text-gray-800 text-lg border border-gray-100 rounded-sm">
            Welcome to <b>RED TIGER WORKSPACE</b>. Start writing...
        </div>
    </div>

    <div id="loading" class="fixed inset-0 bg-black/20 hidden flex items-center justify-center z-50 backdrop-blur-sm">
        <div class="bg-white p-8 rounded-3xl shadow-2xl flex flex-col items-center gap-4">
            <div class="animate-spin rounded-full h-10 w-10 border-4 border-red-600 border-t-transparent"></div>
            <span class="font-bold text-gray-800">TIGER AI IS THINKING...</span>
        </div>
    </div>

    <script>
        const editor = document.getElementById("editor");
        const loading = document.getElementById("loading");

        editor.innerHTML = localStorage.getItem("tiger_word") || "Welcome to <b>RED TIGER WORKSPACE</b>. Start writing...";

        function cmd(n, v=null) {{ document.execCommand(n, false, v); save(); }}
        function save() {{ localStorage.setItem("tiger_word", editor.innerHTML); }}
        editor.oninput = save;

        async function askAI(prompt) {{
            const selectedText = window.getSelection().toString() || editor.innerText;
            if(!selectedText.trim()) return;
            loading.classList.remove('hidden');
            try {{
                const res = await fetch("/api/ai", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{prompt: prompt, content: selectedText}})
                }});
                const data = await res.json();
                if(data.result) {{
                    if(window.getSelection().toString()) {{
                        document.execCommand('insertText', false, data.result);
                    }} else {{
                        editor.innerHTML += `<div class='mt-6 p-6 bg-red-50 border-l-4 border-red-500 rounded-r-xl'>${{data.result}}</div>`;
                    }}
                    save();
                }}
            }} catch(e) {{ alert("Tiger AI error: " + e.message); }}
            loading.classList.add('hidden');
        }}

        function exportPDF() {{
            fetch("/word/pdf", {{
                method: "POST",
                headers: {{"Content-Type": "application/json"}},
                body: JSON.stringify({{html: editor.innerHTML}})
            }}).then(r => r.blob()).then(b => {{
                let a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "Tiger_Doc.pdf"; a.click();
            }});
        }}
    </script>
</body>
</html>
""")

@app.route("/sheet")
def sheet():
    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Tiger Sheet - RED TIGER</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .sheet-container {{ overflow: auto; height: calc(100vh - 125px); }}
        table {{ border-collapse: collapse; }}
        td, th {{ border: 1px solid #edf2f7; min-width: 130px; padding: 6px 12px; font-size: 13px; outline: none; }}
        th {{ background: #fdfdfd; font-weight: 700; color: #4a5568; position: sticky; top: 0; z-index: 10; border-bottom: 2px solid #e2e8f0; }}
        .row-idx {{ min-width: 50px; background: #fdfdfd; font-size: 10px; text-align: center; position: sticky; left: 0; z-index: 20; color: #a0aec0; }}
        td:focus {{ border: 2px solid #e53e3e; background: #fff5f5; z-index: 5; }}
    </style>
</head>
<body class="bg-gray-50">
    {NAV_HTML}
    
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6 sticky top-16 z-40 shadow-sm">
        <div class="flex items-center bg-gray-50 rounded-xl px-4 py-2 w-full max-w-xl border border-gray-100">
            <span class="text-red-500 font-bold italic mr-3">fx</span>
            <input id="formulaBar" type="text" placeholder="Select a cell to edit..." class="bg-transparent w-full outline-none text-sm font-medium">
        </div>
        
        <div class="flex items-center gap-3 bg-gray-50 p-1.5 rounded-xl border border-gray-100">
            <label class="text-[10px] uppercase font-bold text-gray-400 ml-1">Text Color</label>
            <input type="color" id="sheetColorPicker" onchange="applyColor(this.value)" class="w-8 h-8 p-0 border-none cursor-pointer bg-transparent">
        </div>

        <button onclick="exportPDF()" class="bg-red-600 text-white px-6 py-2 rounded-xl hover:bg-red-700 text-sm font-bold shadow-md shadow-red-100 transition whitespace-nowrap">Export PDF</button>
    </div>

    <div class="sheet-container">
        <table id="mainTable"></table>
    </div>

    <script>
        const table = document.getElementById("mainTable");
        const formulaBar = document.getElementById("formulaBar");
        const colorPicker = document.getElementById("sheetColorPicker");
        let activeCell = null;
        const ROWS = 60, COLS = 26;
        
        let head = "<tr><th class='row-idx'>#</th>";
        for(let c=0; c<COLS; c++) head += `<th>${{String.fromCharCode(65+c)}}</th>`;
        table.innerHTML = head + "</tr>";

        for(let r=1; r<=ROWS; r++) {{
            let row = `<tr><td class="row-idx font-bold">${{r}}</td>`;
            for(let c=0; c<COLS; c++) {{
                const cellId = String.fromCharCode(65+c) + r;
                const savedContent = localStorage.getItem('tiger_sheet_html_'+cellId) || "";
                row += `<td contenteditable id="${{cellId}}" onfocus="handleFocus(this)" oninput="handleInput(this)" class="bg-white transition-colors">${{savedContent}}</td>`;
            }}
            table.innerHTML += row + "</tr>";
        }}

        function handleFocus(cell) {{
            activeCell = cell;
            formulaBar.value = cell.innerText;
            const style = window.getComputedStyle(cell);
            const rgb = style.color;
            const hex = rgbToHex(rgb);
            if(hex) colorPicker.value = hex;
        }}

        function handleInput(cell) {{
            localStorage.setItem('tiger_sheet_html_'+cell.id, cell.innerHTML);
            formulaBar.value = cell.innerText;
        }}

        function applyColor(color) {{
            if(activeCell) {{
                activeCell.style.color = color;
                localStorage.setItem('tiger_sheet_html_'+activeCell.id, activeCell.innerHTML);
            }}
        }}

        function rgbToHex(rgb) {{
            const match = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
            if (!match) return null;
            const c = (x) => ("0" + parseInt(x).toString(16)).slice(-2);
            return "#" + c(match[1]) + c(match[2]) + c(match[3]);
        }}

        function exportPDF() {{
             const data = [];
             document.querySelectorAll("tr").forEach((row, rIdx) => {{
                 if(rIdx > 100) return; 
                 const rData = [];
                 row.querySelectorAll("th, td").forEach((cell, cIdx) => {{ 
                     if(cIdx < 16) rData.push(cell.innerText); 
                 }});
                 data.push(rData);
             }});
             fetch("/sheet/pdf", {{
                method: "POST",
                headers: {{"Content-Type": "application/json"}},
                body: JSON.stringify({{data: data}})
            }}).then(r => r.blob()).then(b => {{
                let a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "Tiger_Sheet.pdf"; a.click();
            }});
        }}
    </script>
</body>
</html>
""")

@app.route("/word/pdf", methods=["POST"])
def word_pdf():
    html_data = request.json.get("html", "")
    processed = html_data.replace('<div>', '<br/>').replace('</div>', '')
    
    def convert_span_color(match):
        style = match.group(1)
        color_match = re.search(r'color:\s*(#[0-9a-fA-F]+|rgb\(\d+,\s*\d+,\s*\d+\))', style)
        if color_match:
            return f'<font color="{color_match.group(1)}">'
        return ''

    processed = re.sub(r'<span style="([^"]+)">', convert_span_color, processed)
    processed = processed.replace('</span>', '</font>')
    processed = re.sub(r'<(?!br|p|b|i|u|font|strong|em)[^>]+>', '', processed)
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    p_style = ParagraphStyle('TigerStyle', parent=styles['Normal'], fontSize=12, leading=18, spaceAfter=12, alignment=0)
    
    content = []
    paragraphs = processed.split('<br/>')
    for p in paragraphs:
        if p.strip():
            try:
                content.append(Paragraph(p, p_style))
            except:
                clean_p = re.sub('<[^<]+?>', '', p)
                content.append(Paragraph(clean_p, p_style))
        else:
            content.append(Spacer(1, 0.1*inch))

    doc.build(content)
    buf.seek(0)
    return send_file(buf, download_name="Tiger_Document.pdf", as_attachment=True)

@app.route("/sheet/pdf", methods=["POST"])
def sheet_pdf():
    data = request.json.get("data", [])
    if not data:
        return jsonify({"error": "No data"}), 400

    buf = io.BytesIO()
    # Margins optimize kora hoyeche dynamic wrapping-er jonno
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=30, bottomMargin=30, leftMargin=30, rightMargin=30)
    
    styles = getSampleStyleSheet()
    # Cell text wrapping logic
    cell_style = ParagraphStyle('CellWrap', parent=styles['Normal'], fontSize=8, leading=10, alignment=1)
    header_style = ParagraphStyle('HeaderWrap', parent=styles['Normal'], fontSize=10, leading=12, alignment=1, textColor=colors.whitesmoke, fontName='Helvetica-Bold')

    formatted_data = []
    for r_idx, row in enumerate(data):
        formatted_row = []
        for cell in row:
            if r_idx == 0:
                formatted_row.append(Paragraph(str(cell), header_style))
            else:
                formatted_row.append(Paragraph(str(cell), cell_style))
        formatted_data.append(formatted_row)

    num_cols = len(data[0]) if data else 1
    # Landscape A4 width ~11.69 inch. Margins bad diye ~10.6 inch usable space.
    col_width = (10.6 * inch) / num_cols

    table = Table(formatted_data, colWidths=[col_width] * num_cols)
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e53e3e")), # Red Tiger Header
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff5f5")]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    table.setStyle(style)
    
    doc.build([table])
    buf.seek(0)
    return send_file(buf, download_name="Tiger_Sheet.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
