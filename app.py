import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# In-memory store for now — swap for a DB later.
# Structure: { id: { "data": {...}, "created_at": ..., "filename": ... } }
NOTICES = {}


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NoticeSense AI</title>
<style>
  :root {
    --bg: #0f172a;
    --card: #1e293b;
    --accent: #6366f1;
    --accent-light: #818cf8;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --danger: #ef4444;
    --warning: #f59e0b;
    --success: #22c55e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }
  .container { max-width: 640px; margin: 0 auto; padding: 24px 20px 60px; }
  .screen { display: none; }
  .screen.active { display: block; animation: fadeIn 0.3s ease; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

  nav { display: flex; align-items: center; justify-content: space-between; margin-bottom: 32px; }
  nav .brand { font-weight: 700; font-size: 18px; letter-spacing: -0.02em; }
  nav .brand span { color: var(--accent-light); }
  nav button.nav-link {
    background: none; border: none; color: var(--muted); font-size: 14px; cursor: pointer;
  }

  .hero { text-align: center; padding: 40px 0 32px; }
  .hero h1 { font-size: 30px; line-height: 1.25; margin-bottom: 12px; }
  .hero p { color: var(--muted); font-size: 15px; margin-bottom: 28px; }

  .btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    background: var(--accent); color: white; border: none; border-radius: 10px;
    padding: 13px 22px; font-size: 15px; font-weight: 600; cursor: pointer;
    transition: background 0.15s ease;
  }
  .btn:hover { background: var(--accent-light); }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-block { width: 100%; }
  .btn-secondary { background: var(--card); color: var(--text); border: 1px solid #334155; }

  .card {
    background: var(--card); border: 1px solid #334155; border-radius: 14px;
    padding: 20px; margin-bottom: 14px;
  }
  .card h3 { font-size: 14px; color: var(--muted); margin-bottom: 8px; font-weight: 600; }

  .dropzone {
    border: 2px dashed #334155; border-radius: 14px; padding: 48px 20px;
    text-align: center; cursor: pointer; transition: border-color 0.15s ease, background 0.15s ease;
  }
  .dropzone.dragover { border-color: var(--accent); background: rgba(99,102,241,0.08); }
  .dropzone .icon { font-size: 40px; margin-bottom: 12px; }
  .dropzone p { color: var(--muted); font-size: 14px; margin-bottom: 4px; }
  .dropzone .sub { font-size: 12px; color: #64748b; }
  #fileInput { display: none; }
  #fileNameLabel { margin-top: 14px; font-size: 13px; color: var(--accent-light); min-height: 18px; }

  .checklist { list-style: none; margin: 24px 0; }
  .checklist li { display: flex; align-items: center; gap: 10px; padding: 10px 0; color: var(--muted); font-size: 14px; }
  .checklist li.done { color: var(--text); }
  .checklist li .dot { width: 18px; height: 18px; border-radius: 50%; border: 2px solid #334155; flex-shrink: 0; display:flex; align-items:center; justify-content:center; font-size:11px; }
  .checklist li.done .dot { background: var(--success); border-color: var(--success); color: white; }
  .checklist li.active .dot { border-color: var(--accent); }

  .field-row { display: flex; gap: 10px; padding: 12px 0; border-bottom: 1px solid #334155; }
  .field-row:last-child { border-bottom: none; }
  .field-row .icon { font-size: 18px; flex-shrink: 0; width: 24px; }
  .field-row .label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 3px; }
  .field-row .value { font-size: 15px; }
  .field-row ul { padding-left: 18px; margin-top: 4px; }

  .badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
  .badge.urgent { background: rgba(239,68,68,0.15); color: var(--danger); }
  .badge.important { background: rgba(245,158,11,0.15); color: var(--warning); }
  .badge.normal { background: rgba(34,197,94,0.15); color: var(--success); }

  .notice-card { cursor: pointer; }
  .notice-card .top { display: flex; justify-content: space-between; align-items: start; margin-bottom: 6px; }
  .notice-card h4 { font-size: 16px; }
  .notice-card .meta { font-size: 13px; color: var(--muted); }

  .error-box {
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);
    color: #fca5a5; border-radius: 10px; padding: 14px 16px; font-size: 13px; margin-top: 16px;
  }
  .empty-state { text-align: center; color: var(--muted); padding: 40px 0; font-size: 14px; }
  .spacer { height: 14px; }
</style>
</head>
<body>
<div class="container">

  <nav>
    <div class="brand">Notice<span>Sense</span> AI</div>
    <button class="nav-link" onclick="showScreen('dashboard')">My Notices</button>
  </nav>

  <!-- Screen 1: Home -->
  <section id="screen-home" class="screen active">
    <div class="hero">
      <h1>Turn lengthy notices<br>into clear actions.</h1>
      <p>Upload any notice — exam, placement, event — and get an instant AI summary of what matters.</p>
      <button class="btn" onclick="showScreen('upload')">Upload Notice</button>
    </div>
    <div class="card">
      <h3>Recent Notices</h3>
      <div id="homeRecentList" class="empty-state">No notices analyzed yet.</div>
    </div>
  </section>

  <!-- Screen 2: Upload -->
  <section id="screen-upload" class="screen">
    <h2 style="margin-bottom:20px;">Upload Your Notice</h2>
    <div class="dropzone" id="dropzone" onclick="document.getElementById('fileInput').click()">
      <div class="icon">📄</div>
      <p>Drop notice here or browse files</p>
      <div class="sub">Supported: PDF, JPG, PNG</div>
      <div id="fileNameLabel"></div>
    </div>
    <input type="file" id="fileInput" accept=".pdf,.jpg,.jpeg,.png" />
    <div class="spacer"></div>
    <button class="btn btn-block" id="analyzeBtn" onclick="startAnalysis()" disabled>Analyze Notice</button>
  </section>

  <!-- Screen 3: Processing -->
  <section id="screen-processing" class="screen">
    <div class="hero" style="padding-top:60px;">
      <h1 style="font-size:22px;">Analyzing your notice...</h1>
    </div>
    <ul class="checklist" id="checklist">
      <li data-step="0"><span class="dot"></span> Reading document</li>
      <li data-step="1"><span class="dot"></span> Understanding content</li>
      <li data-step="2"><span class="dot"></span> Extracting important information</li>
      <li data-step="3"><span class="dot"></span> Creating summary</li>
    </ul>
  </section>

  <!-- Screen 4: Result -->
  <section id="screen-result" class="screen">
    <h2 style="margin-bottom:4px;">Notice Analysis</h2>
    <div id="resultTitle" style="color:var(--accent-light); font-size:15px; margin-bottom:20px;"></div>
    <div class="card" id="resultFields"></div>
    <div id="resultError"></div>
    <div class="spacer"></div>
    <button class="btn btn-secondary btn-block" onclick="showScreen('upload'); resetUpload();">Analyze Another</button>
  </section>

  <!-- Screen 5: Dashboard -->
  <section id="screen-dashboard" class="screen">
    <h2 style="margin-bottom:20px;">My Notices</h2>
    <div id="dashboardList" class="empty-state">No notices yet. Upload one to get started.</div>
  </section>

</div>

<script>
let selectedFile = null;
let lastNoticeId = null;

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('screen-' + id).classList.add('active');
  if (id === 'dashboard') refreshNoticeList('dashboardList');
  if (id === 'home') refreshNoticeList('homeRecentList');
}

function resetUpload() {
  selectedFile = null;
  document.getElementById('fileInput').value = '';
  document.getElementById('fileNameLabel').textContent = '';
  document.getElementById('analyzeBtn').disabled = true;
}

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');

fileInput.addEventListener('change', (e) => {
  if (e.target.files.length) handleFile(e.target.files[0]);
});

['dragover', 'dragenter'].forEach(evt =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add('dragover'); })
);
['dragleave', 'drop'].forEach(evt =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); })
);
dropzone.addEventListener('drop', (e) => {
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
  selectedFile = file;
  document.getElementById('fileNameLabel').textContent = file.name;
  document.getElementById('analyzeBtn').disabled = false;
}

async function startAnalysis() {
  if (!selectedFile) return;
  showScreen('processing');
  animateChecklist();

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const res = await fetch('/analyze', { method: 'POST', body: formData });
    const data = await res.json();
    // give the checklist animation a moment to finish for UX
    setTimeout(() => renderResult(data, res.ok), 1600);
  } catch (err) {
    setTimeout(() => renderResult({ error: 'Network error: ' + err.message }, false), 1600);
  }
}

function animateChecklist() {
  const items = document.querySelectorAll('#checklist li');
  items.forEach(li => li.classList.remove('done', 'active'));
  let i = 0;
  const interval = setInterval(() => {
    if (i > 0) items[i - 1].classList.add('done');
    if (i < items.length) items[i].classList.add('active');
    else clearInterval(interval);
    i++;
  }, 380);
}

function renderResult(data, ok) {
  const errorBox = document.getElementById('resultError');
  const fieldsBox = document.getElementById('resultFields');
  const titleBox = document.getElementById('resultTitle');
  fieldsBox.innerHTML = '';
  errorBox.innerHTML = '';

  if (!ok || data.error) {
    titleBox.textContent = 'Analysis failed';
    errorBox.innerHTML = `<div class="error-box">${escapeHtml(data.error || 'Unknown error')}</div>`;
    showScreen('result');
    return;
  }

  lastNoticeId = data.id;
  const fields = data.data || {};
  titleBox.textContent = fields.Title || fields.NoticeType || 'Notice';

  const rows = [
    ['👥', 'Target Audience', fields.TargetAudience],
    ['📅', 'Deadline', fields.Deadline],
    ['🕒', 'Time', fields.Time],
    ['📍', 'Location', fields.Location],
    ['⚠️', 'Action Required', fields.Instructions],
    ['📎', 'Required Documents', fields.RequiredDocuments],
    ['📞', 'Contact', fields.ContactInformation],
  ];

  rows.forEach(([icon, label, value]) => {
    if (!value || (Array.isArray(value) && value.length === 0)) return;
    const valueHtml = Array.isArray(value)
      ? '<ul>' + value.map(v => `<li>${escapeHtml(v)}</li>`).join('') + '</ul>'
      : escapeHtml(value);
    fieldsBox.innerHTML += `
      <div class="field-row">
        <div class="icon">${icon}</div>
        <div>
          <div class="label">${label}</div>
          <div class="value">${valueHtml}</div>
        </div>
      </div>`;
  });

  showScreen('result');
}

async function refreshNoticeList(targetId) {
  const el = document.getElementById(targetId);
  try {
    const res = await fetch('/notices');
    const notices = await res.json();
    if (!notices.length) {
      el.className = 'empty-state';
      el.textContent = 'No notices yet.';
      return;
    }
    el.className = '';
    el.innerHTML = notices.map(n => {
      const urgency = classifyUrgency(n.data.Deadline);
      return `
        <div class="card notice-card">
          <div class="top">
            <h4>${escapeHtml(n.data.Title || n.data.NoticeType || 'Notice')}</h4>
            <span class="badge ${urgency}">${urgency}</span>
          </div>
          <div class="meta">${escapeHtml(n.data.Deadline || 'No deadline')}</div>
        </div>`;
    }).join('');
  } catch (err) {
    el.className = 'empty-state';
    el.textContent = 'Could not load notices.';
  }
}

function classifyUrgency(deadline) {
  if (!deadline) return 'normal';
  const parsed = Date.parse(deadline);
  if (isNaN(parsed)) return 'normal';
  const daysLeft = (parsed - Date.now()) / (1000 * 60 * 60 * 24);
  if (daysLeft <= 3) return 'urgent';
  if (daysLeft <= 10) return 'important';
  return 'normal';
}

function escapeHtml(str) {
  if (str === undefined || str === null) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(INDEX_HTML)


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Accepts a file upload and runs it through the notice-processing pipeline.

    Import is done lazily and defensively: services.notice_processor imports
    services.azure_content, which builds an Azure client at *module load*
    time using DefaultAzureCredential(). If that credential chain isn't
    configured on this machine, importing it raises immediately — which
    would otherwise take the whole Flask app down on startup.

    Doing the import inside the request handler means the app still boots
    and the frontend is fully testable even with zero Azure setup. This is
    a workaround, not a fix — the real fix is not instantiating the client
    at import time in services/azure_content.py.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    uploaded = request.files["file"]
    if uploaded.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    file_bytes = uploaded.read()

    try:
        from services.notice_processor import process_notice
    except Exception as e:
        return jsonify({
            "error": f"Backend AI service is not configured yet ({e.__class__.__name__}: {e}). "
                     "Check with the backend teammate that ENDPOINT/ANALYZER are set and "
                     "Azure credentials (DefaultAzureCredential) are available."
        }), 503

    try:
        notice_data = process_notice(file_bytes)
    except Exception as e:
        return jsonify({
            "error": f"Analysis failed: {e.__class__.__name__}: {e}"
        }), 502

    notice_id = str(uuid.uuid4())
    NOTICES[notice_id] = {
        "data": notice_data,
        "filename": uploaded.filename,
        "created_at": datetime.utcnow().isoformat(),
    }

    return jsonify({"id": notice_id, "data": notice_data})


@app.route("/notices", methods=["GET"])
def list_notices():
    result = [
        {"id": nid, "data": n["data"], "filename": n["filename"], "created_at": n["created_at"]}
        for nid, n in sorted(NOTICES.items(), key=lambda kv: kv[1]["created_at"], reverse=True)
    ]
    return jsonify(result)


@app.route("/notices/<notice_id>", methods=["GET"])
def get_notice(notice_id):
    notice = NOTICES.get(notice_id)
    if not notice:
        return jsonify({"error": "Notice not found."}), 404
    return jsonify(notice)


if __name__ == "__main__":
    app.run(debug=True)