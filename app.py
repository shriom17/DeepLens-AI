import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# In-memory store for now — swap for a DB later.
# Structure: { id: { "data": {...}, "created_at": ..., "filename"/"source": ... } }
NOTICES = {}

# In-memory chat history per document id (demo only, resets on restart)
CHAT_HISTORY = {}


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DeepLensAI</title>
<meta name="description" content="DeepLensAI is an AI-powered document intelligence platform that analyzes PDFs and other documents to extract key information, generate concise summaries, identify important dates and action items, and answer questions through an intelligent AI chatbot.">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">

<style>
:root {
  --bg: #060b14;
  --card: rgba(15, 26, 42, 0.85);
  --card-hover: rgba(20, 34, 54, 0.92);
  --border: rgba(120, 170, 255, 0.14);
  --border-bright: rgba(90, 170, 255, 0.4);
  --text: #eef4fb;
  --text-soft: #9db0c6;
  --text-muted: #62768d;
  --primary: #4f8ff0;
  --primary-light: #7fb0ff;
  --primary-dark: #2a63b8;
  --cyan: #43d6c9;
  --green: #4ade80;
  --yellow: #fbbf24;
  --red: #fb7185;
  --shadow: 0 25px 70px rgba(0,0,0,0.35);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; -webkit-font-smoothing: antialiased; }
body {
  font-family: 'Inter', sans-serif;
  color: var(--text);
  min-height: 100vh;
  background:
    radial-gradient(circle at 12% 0%, rgba(79,143,240,0.16), transparent 32%),
    radial-gradient(circle at 88% 10%, rgba(67,214,201,0.10), transparent 30%),
    var(--bg);
  background-attachment: fixed;
  overflow-x: hidden;
}
body::before {
  content: "";
  position: fixed; inset: 0; pointer-events: none;
  background-image:
    linear-gradient(rgba(100,170,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(100,170,255,0.04) 1px, transparent 1px);
  background-size: 46px 46px;
  mask-image: linear-gradient(to bottom, black 0%, rgba(0,0,0,0.45) 55%, transparent 100%);
  z-index: -1;
}
/* film-grain texture — breaks up the flat gradient surface that reads as generic */
body::after {
  content: "";
  position: fixed; inset: 0; pointer-events: none; z-index: -1;
  opacity: 0.05; mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
button, input, textarea { font-family: inherit; }

.container { width: min(920px, calc(100% - 36px)); margin: 0 auto; padding-bottom: 80px; }
.screen { display: none; }
.screen.active { display: block; animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform: translateY(0); } }

/* NAV */
nav { display:flex; align-items:center; justify-content:space-between; padding: 22px 0; border-bottom: 1px solid var(--border); margin-bottom: 50px; }
.brand { display:flex; align-items:center; gap: 12px; }

/* SIGNATURE: lens/focus-ring mark, ties to "DeepLens" */
.brand .seal {
  width: 42px; height: 42px; border-radius: 50%;
  position: relative;
  background: radial-gradient(circle at 35% 30%, #bfe0ff, #4f8ff0 40%, #14335f 78%, #081428);
  box-shadow: 0 0 22px rgba(79,143,240,0.30);
}
.brand .seal::before {
  content: ""; position: absolute; inset: -6px;
  border-radius: 50%; border: 1.5px solid rgba(79,143,240,0.35);
}
.brand .seal::after {
  content: ""; position: absolute; width: 12px; height: 2px;
  background: rgba(79,143,240,0.55); bottom: -3px; right: -5px;
  transform: rotate(45deg); border-radius: 2px;
}
.brand .name { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 19px; letter-spacing: -0.02em; }
.brand .name em { font-style: normal; color: var(--primary-light); }
.brand .tagline { margin-top: 2px; font-size: 9px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-muted); }

.nav-actions { display:flex; align-items:center; gap: 12px; }
.nav-link {
  background: rgba(79,143,240,0.07); border: 1px solid var(--border); color: var(--text-soft);
  padding: 9px 14px; border-radius: 8px; font-size: 11px; font-weight: 600;
  letter-spacing: 0.05em; text-transform: uppercase; cursor: pointer; transition: 0.2s ease;
}
.nav-link:hover { border-color: var(--border-bright); color: var(--text); background: rgba(79,143,240,0.12); }
.btn-signin {
  background: transparent; border: 1.5px solid var(--primary-light); color: var(--primary-light);
  padding: 10px 18px; border-radius: 8px; font-size: 12px; font-weight: 600;
  letter-spacing: 0.05em; text-transform: uppercase; cursor: pointer; transition: all 0.25s ease;
}
.btn-signin:hover { background: rgba(127,176,255,0.10); border-color: var(--cyan); color: var(--cyan); }
.btn-login {
  background: linear-gradient(135deg, var(--primary-dark), var(--primary));
  border: none; color: white; padding: 10px 18px; border-radius: 8px;
  font-size: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  cursor: pointer; box-shadow: 0 6px 20px rgba(79,143,240,0.25); transition: all 0.25s ease;
}
.btn-login:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(79,143,240,0.35); }

/* AUTH */
.auth-container { max-width: 420px; margin: 60px auto; }
.auth-header { text-align:center; margin-bottom: 36px; }
.auth-header .section-title { margin-bottom: 8px; background: linear-gradient(90deg, var(--primary-light), var(--cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.auth-form { display:flex; flex-direction:column; gap: 18px; }
.form-group { display:flex; flex-direction:column; gap: 8px; }
.form-group label { font-size: 12px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: var(--text-soft); }
.form-group input {
  background: rgba(15,26,42,0.6); border: 1.5px solid var(--border); color: var(--text);
  padding: 12px 15px; border-radius: 9px; font-size: 14px; outline: none; transition: all 0.25s ease;
}
.form-group input::placeholder { color: var(--text-muted); }
.form-group input:focus { border-color: var(--primary-light); box-shadow: 0 0 14px rgba(127,176,255,0.15); }
.auth-divider { text-align:center; margin: 18px 0; position: relative; color: var(--text-muted); font-size: 12px; }
.auth-divider::before, .auth-divider::after { content:""; position:absolute; top:50%; width:45%; height:1px; background: var(--border); }
.auth-divider::before { left:0; } .auth-divider::after { right:0; }
.auth-footer { text-align:center; color: var(--text-soft); font-size: 13px; }
.link-btn { background:none; border:none; color: var(--primary-light); font-weight:700; cursor:pointer; text-decoration: underline; }
.link-btn:hover { color: var(--cyan); }

/* HERO */
.hero { padding: 20px 0 46px; max-width: 760px; position: relative; }
/* Aperture / focus-ring signature — echoes "Lens" concretely instead of decoratively */
.aperture-rings { position: absolute; top: -30px; right: -60px; width: 260px; height: 260px; pointer-events: none; z-index: 0; opacity: 0.55; }
.aperture-rings circle { fill: none; stroke-width: 1; }
.aperture-rings .ring-1 { stroke: rgba(127,176,255,0.35); }
.aperture-rings .ring-2 { stroke: rgba(67,214,201,0.28); stroke-dasharray: 3 6; }
.aperture-rings .ring-3 { stroke: rgba(127,176,255,0.16); }
.aperture-rings .blade { stroke: rgba(67,214,201,0.4); stroke-width: 1.2; transform-origin: 130px 130px; }
@media (max-width: 700px) { .aperture-rings { display: none; } }
.hero .hero-inner { position: relative; z-index: 1; }
.eyebrow { display:inline-flex; align-items:center; gap:8px; font-size:11px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color: var(--primary-light); margin-bottom: 16px; }
.eyebrow::before { content:""; width:7px; height:7px; border-radius:50%; background: var(--cyan); box-shadow: 0 0 12px var(--cyan); }
.hero h1 { font-family:'Space Grotesk', sans-serif; font-size: clamp(34px, 5.6vw, 58px); line-height: 1.06; letter-spacing:-0.04em; margin-bottom: 18px; }
.hero h1 span { background: linear-gradient(90deg, var(--primary-light), var(--cyan)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hero p { color: var(--text-soft); font-size: 15.5px; line-height: 1.7; max-width: 620px; margin-bottom: 28px; }

.btn {
  display:inline-flex; align-items:center; justify-content:center; gap:9px; border:none;
  background: linear-gradient(135deg, var(--primary-dark), var(--primary)); color:white;
  padding: 13px 22px; border-radius: 9px; font-size: 12px; font-weight: 700;
  letter-spacing: 0.05em; text-transform: uppercase; cursor:pointer;
  box-shadow: 0 8px 25px rgba(79,143,240,0.18); transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.btn:hover { transform: translateY(-2px); box-shadow: 0 12px 32px rgba(79,143,240,0.28); }
.btn:disabled { opacity:0.4; cursor:not-allowed; transform:none; }
.btn-block { width: 100%; }
.btn-secondary { background: transparent; border: 1px solid var(--border-bright); color: var(--primary-light); box-shadow:none; }
.btn-secondary:hover { background: rgba(79,143,240,0.08); }

/* FEATURES */
.feature-grid { display:grid; grid-template-columns: repeat(3,1fr); gap: 14px; margin-bottom: 28px; }
.feature { background: rgba(15,26,42,0.55); border: 1px solid var(--border); border-radius: 13px; padding: 20px; transition: 0.2s ease; }
.feature:hover { transform: translateY(-3px); border-color: var(--border-bright); background: var(--card-hover); }
.feature-icon { width:38px; height:38px; display:flex; align-items:center; justify-content:center; border-radius:10px; background: rgba(79,143,240,0.10); color: var(--primary-light); font-size:18px; margin-bottom:14px; }
.feature h4 { font-family:'Space Grotesk', sans-serif; font-size:14px; margin-bottom:7px; }
.feature p { color: var(--text-muted); font-size:12px; line-height:1.55; }
.feature-chat { cursor: pointer; }
.feature-chat:hover { border-color: rgba(67,214,201,0.5); }
.feature-chat:hover .feature-icon { background: rgba(67,214,201,0.14); color: var(--cyan); }
[data-reveal] { opacity: 0; transform: translateY(14px); transition: opacity 0.5s ease, transform 0.5s ease; }
[data-reveal].revealed { opacity: 1; transform: translateY(0); }
@media (prefers-reduced-motion: reduce) {
  [data-reveal] { opacity: 1; transform: none; transition: none; }
}

/* CARDS */
.card { background: linear-gradient(145deg, rgba(20,34,54,0.88), rgba(9,16,28,0.88)); border:1px solid var(--border); border-radius:14px; padding:22px; margin-bottom:15px; box-shadow: var(--shadow); backdrop-filter: blur(14px); position:relative; overflow:hidden; }
.card::before { content:""; position:absolute; top:0; left:0; right:0; height:1px; background: linear-gradient(90deg, transparent, rgba(100,190,255,0.35), transparent); }
.card h3 { font-family:'Space Grotesk', sans-serif; font-size:12px; letter-spacing:0.08em; text-transform:uppercase; color: var(--text-soft); margin-bottom:15px; }

.section-title { font-family:'Space Grotesk', sans-serif; font-size:27px; font-weight:700; letter-spacing:-0.025em; margin-bottom:7px; }
.section-sub { font-size:11px; color: var(--text-muted); letter-spacing:0.08em; text-transform:uppercase; margin-bottom:24px; }

/* SOURCE TABS (file vs url) */
.source-tabs { display:flex; gap:8px; margin-bottom: 18px; }
.source-tab {
  flex:1; padding:11px; text-align:center; border-radius:9px; cursor:pointer;
  border:1px solid var(--border); color: var(--text-muted); font-size:12px; font-weight:600;
  letter-spacing:0.04em; text-transform: uppercase; transition: 0.2s ease; background: rgba(15,26,42,0.4);
}
.source-tab.active { border-color: var(--border-bright); color: var(--primary-light); background: rgba(79,143,240,0.10); }
.source-pane { display:none; }
.source-pane.active { display:block; }

.dropzone {
  border: 1px dashed rgba(100,180,255,0.35); border-radius:14px; padding: 60px 25px; text-align:center; cursor:pointer;
  background: radial-gradient(circle at center, rgba(79,143,240,0.08), transparent 60%), rgba(11,20,34,0.7);
  transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}
.dropzone:hover { border-color: var(--primary); transform: translateY(-2px); }
.dropzone.dragover { border-color: var(--cyan); background: rgba(67,214,201,0.10); }
.dropzone svg { width:48px; height:48px; margin-bottom:15px; stroke: var(--primary-light); filter: drop-shadow(0 0 12px rgba(79,143,240,0.3)); }
.dropzone p { color: var(--text); font-size:15px; font-weight:600; margin-bottom:6px; }
.dropzone .sub { font-size:10px; color: var(--text-muted); letter-spacing:0.08em; }
#fileInput { display:none; }
#fileNameLabel { margin-top:16px; min-height:18px; color: var(--cyan); font-size:12px; font-weight:600; }

.url-pane { padding: 6px 0 0; }
.url-input-row { display:flex; gap:10px; }
.url-input-row input {
  flex:1; background: rgba(11,20,34,0.7); border:1.5px solid var(--border); color:var(--text);
  padding: 13px 16px; border-radius:10px; font-size:14px; outline:none; transition: 0.2s ease;
}
.url-input-row input:focus { border-color: var(--primary-light); box-shadow: 0 0 14px rgba(127,176,255,0.15); }
.url-hint { font-size: 11px; color: var(--text-muted); margin-top: 10px; }

/* PROCESSING */
.processing-wrap { padding: 65px 0; text-align:center; }
.processing-wrap h1 { font-family:'Space Grotesk', sans-serif; font-size:27px; margin-bottom:8px; }
.processing-wrap .section-sub { text-align:center; }
.ai-orb {
  width:88px; height:88px; margin:0 auto 26px; border-radius:50%;
  background: radial-gradient(circle at 35% 30%, #bfe0ff, #4f8ff0 35%, #17427f 70%, #081428);
  box-shadow: 0 0 24px rgba(79,143,240,0.35), 0 0 76px rgba(67,214,201,0.12);
  animation: pulseOrb 1.8s ease-in-out infinite;
}
@keyframes pulseOrb { 0%,100% { transform: scale(0.92); } 50% { transform: scale(1.05); } }

.checklist { list-style:none; margin: 28px auto 0; max-width: 420px; text-align:left; }
.checklist li { display:flex; align-items:center; gap:12px; padding:13px 0; color: var(--text-muted); font-size:13px; border-bottom:1px solid rgba(100,180,255,0.08); transition: 0.2s ease; }
.checklist li:last-child { border-bottom:none; }
.checklist li.active { color: var(--primary-light); }
.checklist li.done { color: var(--green); }
.checklist li .box { width:19px; height:19px; border-radius:6px; border:1px solid rgba(100,180,255,0.25); flex-shrink:0; display:flex; align-items:center; justify-content:center; }
.checklist li.active .box { border-color: var(--primary); box-shadow: 0 0 11px rgba(79,143,240,0.25); }
.checklist li.done .box { border-color: var(--green); background: rgba(74,222,128,0.10); color: var(--green); }
.checklist li.done .box::after { content:"✓"; }

/* RESULT */
.ref-code { color: var(--text-muted); font-size:10px; letter-spacing:0.08em; margin-bottom:16px; }
.doc-card { padding: 25px; overflow: hidden; }

/* stamp -> lens focus mark, matches brand */
.stamp {
  position:absolute; top:18px; right:18px; width:100px; height:100px; border-radius:50%;
  display:flex; align-items:center; justify-content:center; color: var(--cyan);
  border: 1px solid rgba(67,214,201,0.5); background: rgba(67,214,201,0.05);
  transform: rotate(-8deg) scale(0.5); opacity:0;
  transition: transform 0.45s cubic-bezier(.2,1.4,.4,1), opacity 0.3s ease; pointer-events:none;
  box-shadow: 0 0 22px rgba(67,214,201,0.10);
}
.stamp.show { transform: rotate(-8deg) scale(1); opacity: 0.9; }
.stamp-inner { text-align:center; font-size:8px; font-weight:700; letter-spacing:0.1em; }
.stamp-inner strong { display:block; font-family:'Space Grotesk', sans-serif; font-size:16px; margin-bottom:3px; }

.field-row { display:flex; gap:14px; padding:15px 0; border-bottom:1px solid rgba(100,180,255,0.09); }
.field-row:last-child { border-bottom:none; }
.field-row .icon { width:22px; flex-shrink:0; margin-top:2px; }
.field-row .icon svg { width:18px; height:18px; stroke: var(--primary-light); fill:none; }
.field-row .label { color: var(--text-muted); font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:5px; }
.field-row .value { color: var(--text); font-size:14px; line-height:1.55; }
.field-row ul { padding-left:18px; margin-top:4px; }

.badge { display:inline-flex; align-items:center; padding:4px 9px; border-radius:20px; font-size:9px; font-weight:700; letter-spacing:0.07em; text-transform:uppercase; border:1px solid; }
.badge.urgent { color: var(--red); border-color: rgba(251,113,133,0.4); background: rgba(251,113,133,0.08); }
.badge.important { color: var(--yellow); border-color: rgba(251,191,36,0.35); background: rgba(251,191,36,0.08); }
.badge.normal { color: var(--green); border-color: rgba(74,222,128,0.35); background: rgba(74,222,128,0.08); }

.notice-card { cursor:pointer; transition: transform 0.18s ease, border-color 0.18s ease; }
.notice-card:hover { transform: translateY(-2px); border-color: var(--border-bright); }
.notice-card .top { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:8px; }
.notice-card h4 { font-family:'Space Grotesk', sans-serif; font-size:15px; font-weight:600; }
.notice-card .meta { color: var(--text-muted); font-size:10px; letter-spacing:0.04em; }

.error-box { background: rgba(251,113,133,0.08); border:1px solid rgba(251,113,133,0.45); color:#ff9aaa; border-radius:10px; padding:15px 17px; font-size:12px; margin-top:16px; line-height:1.6; }
.empty-state { text-align:center; color: var(--text-muted); padding:32px 0; font-size:12px; }
.spacer { height:15px; }
.footer { margin-top:46px; padding-top:20px; border-top:1px solid var(--border); text-align:center; color: var(--text-muted); font-size:10px; letter-spacing:0.05em; }

/* CHATBOT WIDGET */
#chatToggle {
  position: fixed; bottom: 24px; right: 24px; width: 58px; height: 58px; border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-dark), var(--cyan)); border:none; cursor:pointer;
  display:flex; align-items:center; justify-content:center; box-shadow: 0 10px 30px rgba(79,143,240,0.35);
  z-index: 40; transition: transform 0.2s ease;
}
#chatToggle:hover { transform: translateY(-3px) scale(1.03); }
#chatToggle svg { width:26px; height:26px; stroke:white; fill:none; position: relative; z-index: 1; }
#chatToggle::before {
  content: ""; position: absolute; inset: -6px; border-radius: 50%;
  border: 1.5px solid var(--cyan); opacity: 0; animation: chatPulse 2.6s ease-out infinite;
}
@keyframes chatPulse {
  0% { opacity: 0.6; transform: scale(0.85); }
  70% { opacity: 0; transform: scale(1.35); }
  100% { opacity: 0; transform: scale(1.35); }
}
@media (prefers-reduced-motion: reduce) { #chatToggle::before { animation: none; } }
#chatPanel {
  position: fixed; bottom: 94px; right: 24px; width: 340px; max-width: calc(100vw - 32px);
  height: 460px; max-height: calc(100vh - 140px);
  background: linear-gradient(165deg, rgba(20,34,54,0.97), rgba(8,15,26,0.98));
  border: 1px solid var(--border-bright); border-radius: 16px; box-shadow: var(--shadow);
  display: none; flex-direction: column; overflow: hidden; z-index: 40; backdrop-filter: blur(18px);
}
#chatPanel.open { display: flex; animation: fadeIn 0.25s ease; }
.chat-header { padding: 14px 16px; border-bottom: 1px solid var(--border); display:flex; align-items:center; justify-content:space-between; }
.chat-header .title { display:flex; align-items:center; gap:9px; font-family:'Space Grotesk', sans-serif; font-weight:600; font-size:13px; }
.chat-header .dot { width:7px; height:7px; border-radius:50%; background: var(--cyan); box-shadow: 0 0 8px var(--cyan); }
.chat-close { background:none; border:none; color: var(--text-muted); cursor:pointer; font-size:16px; padding:4px; }
.chat-close:hover { color: var(--text); }
.chat-messages { flex:1; overflow-y:auto; padding: 14px 16px; display:flex; flex-direction:column; gap:12px; }
.chat-msg { max-width: 85%; padding: 10px 13px; border-radius: 12px; font-size: 12.5px; line-height:1.5; }
.chat-msg.bot { align-self:flex-start; background: rgba(79,143,240,0.10); border: 1px solid var(--border); color: var(--text); border-bottom-left-radius: 3px; }
.chat-msg.user { align-self:flex-end; background: linear-gradient(135deg, var(--primary-dark), var(--primary)); color:white; border-bottom-right-radius: 3px; }
.chat-msg.error-msg { align-self:flex-start; background: rgba(251,113,133,0.08); border:1px solid rgba(251,113,133,0.35); color:#ff9aaa; }
.chat-input-row { display:flex; gap:8px; padding: 12px; border-top: 1px solid var(--border); }
.chat-input-row input {
  flex:1; background: rgba(11,20,34,0.7); border:1px solid var(--border); color:var(--text);
  padding: 10px 13px; border-radius: 9px; font-size:13px; outline:none;
}
.chat-input-row input:focus { border-color: var(--primary-light); }
.chat-send {
  width:38px; height:38px; border-radius:9px; border:none; flex-shrink:0;
  background: linear-gradient(135deg, var(--primary-dark), var(--primary)); color:white; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
}
.chat-send svg { width:16px; height:16px; }
.chat-context {
  font-size: 10px; color: var(--text-muted); padding: 8px 16px; border-bottom: 1px solid var(--border);
  background: rgba(79,143,240,0.05);
}

@media (max-width: 700px) {
  .container { width: min(100% - 26px, 920px); }
  nav { margin-bottom: 32px; flex-wrap: wrap; }
  .nav-actions { width:100%; gap:8px; margin-top:12px; }
  .btn-signin, .btn-login { flex:1; padding:10px 12px; font-size:11px; }
  .hero h1 { font-size: 36px; }
  .feature-grid { grid-template-columns: 1fr; }
  .stamp { width:78px; height:78px; top:15px; right:12px; }
  .doc-card { padding:20px; }
  #chatPanel { right: 12px; left: 12px; width: auto; bottom: 88px; }
  #chatToggle { right: 16px; bottom: 16px; }
}
</style>
</head>
<body>
<div class="container">

  <nav>
    <div class="brand">
      <div class="seal"></div>
      <div>
        <div class="name">Deep<em>Lens</em>AI</div>
        <div class="tagline">AI document intelligence</div>
      </div>
    </div>
    <div class="nav-actions">
      <button class="nav-link" onclick="showScreen('dashboard')">My Documents</button>
      <button class="btn-signin" onclick="showScreen('signin')">Sign In</button>
      <button class="btn-login" onclick="showScreen('login')">Log In</button>
    </div>
  </nav>

  <!-- HOME -->
  <section id="screen-home" class="screen active">
    <div class="hero">
      <svg class="aperture-rings" viewBox="0 0 260 260" aria-hidden="true">
        <circle class="ring-1" cx="130" cy="130" r="110"/>
        <circle class="ring-2" cx="130" cy="130" r="82"/>
        <circle class="ring-3" cx="130" cy="130" r="54"/>
        <g id="apertureBlades"></g>
      </svg>
      <div class="hero-inner">
        <div class="eyebrow">AI Document Intelligence</div>
        <h1>See through any document<br><span>in seconds.</span></h1>
        <p>DeepLensAI is an AI-powered document intelligence platform that analyzes PDFs and other documents to extract key information, generate concise summaries, identify important dates and action items, and answer questions through an intelligent AI chatbot.</p>
        <button class="btn" onclick="showScreen('upload')">Analyze a Document</button>
      </div>
    </div>

    <div class="feature-grid">
      <div class="feature" data-reveal>
        <div class="feature-icon">🔍</div>
        <h4>Understand</h4>
        <p>DeepLensAI reads the full document and understands what it's actually about.</p>
      </div>
      <div class="feature" data-reveal>
        <div class="feature-icon">🧠</div>
        <h4>Extract</h4>
        <p>Key facts, dates, people, and instructions are pulled out automatically.</p>
      </div>
      <div class="feature feature-chat" data-reveal onclick="toggleChat()">
        <div class="feature-icon">💬</div>
        <h4>Ask the AI Chatbot</h4>
        <p>Open the assistant and ask questions about any document you've analyzed.</p>
      </div>
    </div>

    <div class="card">
      <h3>Recently Analyzed</h3>
      <div id="homeRecentList" class="empty-state">No documents analyzed yet.</div>
    </div>
  </section>

  <!-- SIGN IN / LOG IN (cosmetic only — not wired to a real backend) -->
  <section id="screen-signin" class="screen">
    <div class="auth-container">
      <div class="auth-header">
        <h2 class="section-title">Create Account</h2>
        <div class="section-sub">Join DeepLensAI to get started</div>
      </div>
      <form class="auth-form" id="signupForm">
        <div class="form-group"><label for="signupEmail">Email Address</label><input type="email" id="signupEmail" placeholder="you@example.com" required></div>
        <div class="form-group"><label for="signupPassword">Password</label><input type="password" id="signupPassword" placeholder="At least 8 characters" required></div>
        <div class="form-group"><label for="signupConfirm">Confirm Password</label><input type="password" id="signupConfirm" placeholder="Confirm your password" required></div>
        <button type="submit" class="btn btn-block">Create Account</button>
      </form>
      <div class="auth-divider">or</div>
      <div class="auth-footer">Already have an account?<button class="link-btn" onclick="showScreen('login')">Log In</button></div>
    </div>
  </section>

  <section id="screen-login" class="screen">
    <div class="auth-container">
      <div class="auth-header">
        <h2 class="section-title">Welcome Back</h2>
        <div class="section-sub">Log in to access your documents</div>
      </div>
      <form class="auth-form" id="loginForm">
        <div class="form-group"><label for="loginEmail">Email Address</label><input type="email" id="loginEmail" placeholder="you@example.com" required></div>
        <div class="form-group"><label for="loginPassword">Password</label><input type="password" id="loginPassword" placeholder="Enter your password" required></div>
        <button type="submit" class="btn btn-block">Log In</button>
      </form>
      <div class="auth-divider">or</div>
      <div class="auth-footer">Don't have an account?<button class="link-btn" onclick="showScreen('signin')">Sign Up</button></div>
    </div>
  </section>

  <!-- UPLOAD -->
  <section id="screen-upload" class="screen">
    <h2 class="section-title">Analyze a Document</h2>
    <div class="section-sub">Upload a file or paste a link</div>

    <div class="source-tabs">
      <div class="source-tab active" id="tabFile" onclick="switchSource('file')">Upload File</div>
      <div class="source-tab" id="tabUrl" onclick="switchSource('url')">Paste URL</div>
    </div>

    <div class="source-pane active" id="paneFile">
      <div class="dropzone" id="dropzone" onclick="document.getElementById('fileInput').click()">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/>
          <path d="M12 3v11"/>
          <path d="M7 8l5-5 5 5"/>
        </svg>
        <p>Drop your document here</p>
        <div class="sub">or click to browse</div>
        <div class="sub" style="margin-top:10px;">PDF · JPG · PNG</div>
        <div id="fileNameLabel"></div>
      </div>
      <input type="file" id="fileInput" accept=".pdf,.jpg,.jpeg,.png" />
    </div>

    <div class="source-pane" id="paneUrl">
      <div class="url-pane">
        <div class="url-input-row">
          <input type="url" id="urlInput" placeholder="https://example.com/document.pdf" oninput="onUrlInput()">
        </div>
        <div class="url-hint">DeepLensAI will fetch and read the document at this link.</div>
      </div>
    </div>

    <div class="spacer"></div>
    <button class="btn btn-block" id="analyzeBtn" onclick="startAnalysis()" disabled>Analyze With AI</button>
  </section>

  <!-- PROCESSING -->
  <section id="screen-processing" class="screen">
    <div class="processing-wrap">
      <div class="ai-orb"></div>
      <div class="eyebrow">AI Processing</div>
      <h1>Reading your document…</h1>
      <div class="section-sub">DeepLensAI is analyzing the content</div>
      <ul class="checklist" id="checklist">
        <li data-step="0"><span class="box"></span>Reading document</li>
        <li data-step="1"><span class="box"></span>Understanding content</li>
        <li data-step="2"><span class="box"></span>Extracting key information</li>
        <li data-step="3"><span class="box"></span>Creating summary</li>
      </ul>
    </div>
  </section>

  <!-- RESULT -->
  <section id="screen-result" class="screen">
    <h2 class="section-title" id="resultTitle">Document Analysis</h2>
    <div class="ref-code" id="resultRef"></div>
    <div class="card doc-card" id="resultCardWrap">
      <div class="stamp" id="stampMark">
        <div class="stamp-inner"><strong>AI</strong>READ<br>BY<br>DEEPLENS</div>
      </div>
      <div id="resultFields"></div>
    </div>
    <div id="resultError"></div>
    <div class="spacer"></div>
    <button class="btn btn-secondary btn-block" onclick="showScreen('upload'); resetUpload();">Analyze Another Document</button>
  </section>

  <!-- DASHBOARD -->
  <section id="screen-dashboard" class="screen">
    <h2 class="section-title">My Documents</h2>
    <div class="section-sub">Everything you've analyzed</div>
    <div id="dashboardList" class="empty-state">No documents yet.<br><br>Analyze your first document to get started.</div>
  </section>

  <div class="footer">DeepLensAI · AI Document Intelligence</div>
</div>

<!-- CHATBOT WIDGET -->
<button id="chatToggle" onclick="toggleChat()" aria-label="Open AI chat">
  <svg viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
  </svg>
</button>

<div id="chatPanel">
  <div class="chat-header">
    <div class="title"><span class="dot"></span> DeepLensAI Assistant</div>
    <button class="chat-close" onclick="toggleChat()">✕</button>
  </div>
  <div class="chat-context" id="chatContext">Ask me anything — I can dig deeper into a document you've analyzed.</div>
  <div class="chat-messages" id="chatMessages">
    <div class="chat-msg bot">Hi! Analyze a document first, then ask me questions about it — or ask me anything in general.</div>
  </div>
  <div class="chat-input-row">
    <input type="text" id="chatInput" placeholder="Ask a question..." onkeydown="if(event.key==='Enter') sendChat();">
    <button class="chat-send" onclick="sendChat()" aria-label="Send">
      <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4 20-7z"/>
      </svg>
    </button>
  </div>
</div>

<script>
let selectedFile = null;
let selectedUrl = null;
let activeSource = 'file';
let lastNoticeId = null;

/* SCREEN NAV */
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const target = document.getElementById('screen-' + id);
  if (target) target.classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (id === 'dashboard') refreshNoticeList('dashboardList');
  if (id === 'home') refreshNoticeList('homeRecentList');
}

function resetUpload() {
  selectedFile = null;
  selectedUrl = null;
  document.getElementById('fileInput').value = '';
  document.getElementById('fileNameLabel').textContent = '';
  document.getElementById('urlInput').value = '';
  document.getElementById('analyzeBtn').disabled = true;
  document.getElementById('stampMark').classList.remove('show');
  switchSource('file');
}

/* SOURCE TABS */
function switchSource(source) {
  activeSource = source;
  document.getElementById('tabFile').classList.toggle('active', source === 'file');
  document.getElementById('tabUrl').classList.toggle('active', source === 'url');
  document.getElementById('paneFile').classList.toggle('active', source === 'file');
  document.getElementById('paneUrl').classList.toggle('active', source === 'url');
  updateAnalyzeState();
}

function updateAnalyzeState() {
  const btn = document.getElementById('analyzeBtn');
  if (activeSource === 'file') btn.disabled = !selectedFile;
  else btn.disabled = !selectedUrl;
}

function onUrlInput() {
  const val = document.getElementById('urlInput').value.trim();
  selectedUrl = val.length > 0 ? val : null;
  updateAnalyzeState();
}

/* AUTH FORMS (cosmetic — no real backend) */
const signupForm = document.getElementById('signupForm');
if (signupForm) {
  signupForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const password = document.getElementById('signupPassword').value;
    const confirm = document.getElementById('signupConfirm').value;
    if (password !== confirm) { alert('Passwords do not match!'); return; }
    if (password.length < 8) { alert('Password must be at least 8 characters!'); return; }
    alert('Account created! Please log in.');
    signupForm.reset();
    showScreen('login');
  });
}
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', function(e) {
    e.preventDefault();
    alert('Logged in!');
    loginForm.reset();
    showScreen('home');
  });
}

/* FILE UPLOAD */
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', (e) => { if (e.target.files.length) handleFile(e.target.files[0]); });
['dragover', 'dragenter'].forEach(evt => dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.add('dragover'); }));
['dragleave', 'drop'].forEach(evt => dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.remove('dragover'); }));
dropzone.addEventListener('drop', e => { if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); });

function handleFile(file) {
  const allowed = ['application/pdf', 'image/jpeg', 'image/png'];
  if (!allowed.includes(file.type)) { alert('Please upload a PDF, JPG or PNG file.'); return; }
  selectedFile = file;
  document.getElementById('fileNameLabel').textContent = '✓ ' + file.name;
  updateAnalyzeState();
}

/* ANALYSIS */
async function startAnalysis() {
  if (activeSource === 'file' && !selectedFile) return;
  if (activeSource === 'url' && !selectedUrl) return;

  showScreen('processing');
  animateChecklist();

  try {
    let response;
    if (activeSource === 'file') {
      const formData = new FormData();
      formData.append('file', selectedFile);
      response = await fetch('/analyze', { method: 'POST', body: formData });
    } else {
      response = await fetch('/analyze-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: selectedUrl })
      });
    }
    const data = await response.json();
    setTimeout(() => renderResult(data, response.ok), 1500);
  } catch (error) {
    setTimeout(() => renderResult({ error: 'Network error: ' + error.message }, false), 1500);
  }
}

function animateChecklist() {
  const items = document.querySelectorAll('#checklist li');
  items.forEach(i => i.classList.remove('done', 'active'));
  let idx = 0;
  const interval = setInterval(() => {
    if (idx > 0) items[idx - 1].classList.add('done');
    if (idx < items.length) items[idx].classList.add('active');
    else clearInterval(interval);
    idx++;
  }, 380);
}

function refCode(id) {
  const year = new Date().getFullYear();
  const short = (id || '').replace(/-/g, '').slice(0, 6).toUpperCase();
  return `REF DL-${year}-${short || '000000'}`;
}

/* Schema-agnostic result rendering: iterates whatever fields the backend
   returns instead of assuming a fixed notice schema, so this keeps working
   regardless of document type. */
const FIELD_ICON_MAP = {
  title: 'doc', documenttype: 'doc',
  targetaudience: 'audience', audience: 'audience',
  deadline: 'calendar', date: 'calendar', keydates: 'calendar',
  time: 'clock',
  location: 'pin',
  instructions: 'flag', actionitems: 'flag', actionrequired: 'flag',
  requireddocuments: 'paperclip', documents: 'paperclip',
  contactinformation: 'phone', contact: 'phone',
  summary: 'doc', aisummary: 'doc'
};
const LABEL_OVERRIDES = { targetaudience: 'Target Audience', requireddocuments: 'Required Documents', contactinformation: 'Contact', actionitems: 'Action Items', aisummary: 'Summary', documenttype: 'Document Type' };

function humanizeKey(key) {
  if (LABEL_OVERRIDES[key.toLowerCase()]) return LABEL_OVERRIDES[key.toLowerCase()];
  return key.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/_/g, ' ').replace(/^\\w/, c => c.toUpperCase());
}

function renderResult(data, ok) {
  const errorBox = document.getElementById('resultError');
  const fieldsBox = document.getElementById('resultFields');
  const titleBox = document.getElementById('resultTitle');
  const refBox = document.getElementById('resultRef');
  const stamp = document.getElementById('stampMark');
  fieldsBox.innerHTML = ''; errorBox.innerHTML = ''; refBox.textContent = '';
  stamp.classList.remove('show');

  if (!ok || data.error) {
    titleBox.textContent = 'Analysis Failed';
    errorBox.innerHTML = `<div class="error-box">${escapeHtml(data.error || 'Unknown error')}</div>`;
    showScreen('result');
    return;
  }

  lastNoticeId = data.id;
  const fields = data.data || {};
  const titleKey = Object.keys(fields).find(k => k.toLowerCase() === 'title') ||
                   Object.keys(fields).find(k => k.toLowerCase().includes('type'));
  titleBox.textContent = (titleKey && fields[titleKey]) || 'Document';
  refBox.textContent = refCode(data.id);

  Object.keys(fields).forEach(key => {
    if (key === titleKey) return;
    const value = fields[key];
    if (!value || (Array.isArray(value) && value.length === 0)) return;
    const iconName = FIELD_ICON_MAP[key.toLowerCase()] || 'doc';
    const valueHtml = Array.isArray(value)
      ? '<ul>' + value.map(v => `<li>${escapeHtml(v)}</li>`).join('') + '</ul>'
      : escapeHtml(value);
    fieldsBox.innerHTML += `
      <div class="field-row">
        <div class="icon">${fieldIcon(iconName)}</div>
        <div>
          <div class="label">${humanizeKey(key)}</div>
          <div class="value">${valueHtml}</div>
        </div>
      </div>`;
  });

  if (!fieldsBox.innerHTML) {
    fieldsBox.innerHTML = `<div class="empty-state">No structured fields returned.</div>`;
  }

  showScreen('result');
  requestAnimationFrame(() => setTimeout(() => stamp.classList.add('show'), 120));
}

function fieldIcon(name) {
  const icons = {
    audience: '<circle cx="9" cy="7" r="3"/><path d="M2 20c0-4 3-6 7-6s7 2 7 6"/><path d="M16 8a3 3 0 0 1 0 6"/><path d="M18.5 14.5c2 .5 3.5 2 3.5 5.5"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="1"/><path d="M3 10h18"/><path d="M8 3v4"/><path d="M16 3v4"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    pin: '<path d="M12 21s7-6.5 7-12a7 7 0 1 0-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="9" r="2.3"/>',
    flag: '<path d="M5 3v18"/><path d="M5 4h11l-2.5 4L16 12H5"/>',
    paperclip: '<path d="M18 10 9.5 18.5a4 4 0 0 1-5.66-5.66L13 3.68A2.7 2.7 0 1 1 16.8 7.5L8 16.3"/>',
    phone: '<path d="M5 4h4l1.5 4.5L8 10.5a11 11 0 0 0 5.5 5.5l1.9-2.5 4.5 1.5v4a2 2 0 0 1-2.2 2A17 17 0 0 1 3 6.2 2 2 0 0 1 5 4z"/>',
    doc: '<path d="M14 3v5a1 1 0 0 0 1 1h5"/><path d="M6 3h8l6 6v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>'
  };
  return `<svg viewBox="0 0 24 24" fill="none" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${icons[name] || icons.doc}</svg>`;
}

/* DASHBOARD */
async function refreshNoticeList(targetId) {
  const el = document.getElementById(targetId);
  try {
    const res = await fetch('/notices');
    const list = await res.json();
    if (!list.length) { el.className = 'empty-state'; el.innerHTML = 'No documents yet.'; return; }
    el.className = '';
    el.innerHTML = list.map(item => {
      const fields = item.data || {};
      const titleKey = Object.keys(fields).find(k => k.toLowerCase() === 'title') || Object.keys(fields).find(k => k.toLowerCase().includes('type'));
      const dateKey = Object.keys(fields).find(k => ['deadline', 'date'].includes(k.toLowerCase()));
      const title = (titleKey && fields[titleKey]) || item.filename || item.source || 'Document';
      const urgency = classifyUrgency(dateKey ? fields[dateKey] : null);
      return `
        <div class="card notice-card">
          <div class="top">
            <h4>${escapeHtml(title)}</h4>
            <span class="badge ${urgency}">${urgency}</span>
          </div>
          <div class="meta">${escapeHtml((dateKey && fields[dateKey]) || 'No date')} · ${refCode(item.id)}</div>
        </div>`;
    }).join('');
  } catch (e) {
    el.className = 'empty-state';
    el.textContent = 'Could not load documents.';
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

/* CHATBOT */
function toggleChat() {
  document.getElementById('chatPanel').classList.toggle('open');
  const ctx = document.getElementById('chatContext');
  ctx.textContent = lastNoticeId
    ? 'Chatting about your most recently analyzed document.'
    : 'Ask me anything — I can dig deeper into a document you\\'ve analyzed.';
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;
  appendChatMsg(text, 'user');
  input.value = '';

  const messages = document.getElementById('chatMessages');
  const thinking = document.createElement('div');
  thinking.className = 'chat-msg bot';
  thinking.textContent = '…';
  messages.appendChild(thinking);
  messages.scrollTop = messages.scrollHeight;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, document_id: lastNoticeId })
    });
    const data = await res.json();
    thinking.remove();
    if (!res.ok || data.error) {
      appendChatMsg(data.error || 'Something went wrong.', 'error-msg');
    } else {
      appendChatMsg(data.reply, 'bot');
    }
  } catch (e) {
    thinking.remove();
    appendChatMsg('Network error: ' + e.message, 'error-msg');
  }
}

function appendChatMsg(text, cls) {
  const messages = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'chat-msg ' + cls;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

/* AI aperture blades — draws camera-aperture-style radial lines behind the
   hero heading, so the "Lens" name has a real visual referent instead of
   being purely decorative. */
(function drawApertureBlades() {
  const group = document.getElementById('apertureBlades');
  if (!group) return;
  const bladeCount = 8;
  const cx = 130, cy = 130, r1 = 40, r2 = 54;
  for (let i = 0; i < bladeCount; i++) {
    const angle = (i / bladeCount) * Math.PI * 2;
    const x1 = cx + r1 * Math.cos(angle);
    const y1 = cy + r1 * Math.sin(angle);
    const x2 = cx + r2 * Math.cos(angle);
    const y2 = cy + r2 * Math.sin(angle);
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1); line.setAttribute('y1', y1);
    line.setAttribute('x2', x2); line.setAttribute('y2', y2);
    line.setAttribute('class', 'blade');
    group.appendChild(line);
  }
})();

/* Scroll-reveal for feature cards — a single orchestrated moment on load
   rather than scattered hover effects. Respects prefers-reduced-motion via CSS. */
(function initReveal() {
  const items = document.querySelectorAll('[data-reveal]');
  if (!items.length) return;
  if (!('IntersectionObserver' in window)) {
    items.forEach(el => el.classList.add('revealed'));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => entry.target.classList.add('revealed'), i * 90);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });
  items.forEach(el => observer.observe(el));
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template_string(INDEX_HTML)


def _store_result(notice_data, source_label):
    doc_id = str(uuid.uuid4())
    NOTICES[doc_id] = {
        "data": notice_data,
        "filename": source_label,
        "created_at": datetime.utcnow().isoformat(),
    }
    return doc_id


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    File-upload analysis. Imports the Azure pipeline lazily so the frontend
    still boots even when Azure credentials (DefaultAzureCredential) aren't
    configured on this machine.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    uploaded = request.files["file"]
    if uploaded.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    file_bytes = uploaded.read()

    try:
      from backend.services.notice_processor import process_notice
    except Exception as e:
        return jsonify({
            "error": f"Backend AI service is not configured yet ({e.__class__.__name__}: {e}). "
                     "Check that ENDPOINT/ANALYZER are set and Azure credentials are available."
        }), 503

    try:
        notice_data = process_notice(file_bytes)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {e.__class__.__name__}: {e}"}), 502

    doc_id = _store_result(notice_data, uploaded.filename)
    return jsonify({"id": doc_id, "data": notice_data})


@app.route("/analyze-url", methods=["POST"])
def analyze_url():
    """
    URL-based analysis. Delegates URL processing to notice_processor,
    which routes between Azure and Gemini pipelines by AI_PROVIDER.

    SECURITY NOTE: fetching an arbitrary user-supplied URL from the server
    is an SSRF surface (it could be pointed at internal/private addresses).
    This does no allowlisting or private-IP blocking — acceptable for a
    local demo, not for a deployed service. If this ever goes further than
    a classroom project, add URL validation before the request.
    """
    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or "").strip()

    if not url:
        return jsonify({"error": "No URL provided."}), 400
    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    try:
      from backend.services.notice_processor import process_notice_url
    except Exception as e:
        return jsonify({
        "error": f"Backend document service is not configured yet ({e.__class__.__name__}: {e}). "
             "Check provider settings and required credentials in .env."
        }), 503

    try:
      notice_data = process_notice_url(url)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {e.__class__.__name__}: {e}"}), 502

    doc_id = _store_result(notice_data, url)
    return jsonify({"id": doc_id, "data": notice_data})


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


@app.route("/chat", methods=["POST"])
def chat():
    """
    Chatbot endpoint. Lazily imports the generative AI service so the
    frontend still works even when it's an empty stub — right now it is,
    so this will return a 503 until services/generative_ai.py is built out.

    Expected contract once implemented: generative_ai.answer_question(
        message: str, document_context: dict | None
    ) -> str
    """
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    document_id = payload.get("document_id")

    if not message:
        return jsonify({"error": "No message provided."}), 400

    document_context = None
    if document_id and document_id in NOTICES:
        document_context = NOTICES[document_id]["data"]

    try:
      from backend.services.generative_ai import answer_question
    except Exception as e:
        return jsonify({
            "error": f"Chat isn't wired up yet ({e.__class__.__name__}: {e}). "
                     "services/generative_ai.py needs an answer_question() function "
                     "backed by Azure OpenAI before this works."
        }), 503

    try:
        reply = answer_question(message, document_context)
    except Exception as e:
        return jsonify({"error": f"Chat failed: {e.__class__.__name__}: {e}"}), 502

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)