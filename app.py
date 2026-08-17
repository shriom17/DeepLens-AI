import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# In-memory store for now — swap for a DB later.
# Structure:
# {
#   id: {
#       "data": {...},
#       "created_at": ...,
#       "filename": ...
#   }
# }
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

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<link
href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap"
rel="stylesheet">

<style>

:root {
    --bg: #06101d;
    --bg-secondary: #09182a;

    --card: rgba(13, 29, 48, 0.82);
    --card-hover: rgba(18, 39, 64, 0.92);

    --border: rgba(111, 180, 255, 0.16);
    --border-bright: rgba(77, 163, 255, 0.42);

    --text: #edf6ff;
    --text-soft: #9db1c7;
    --text-muted: #6f849b;

    --primary: #4da3ff;
    --primary-light: #70bbff;
    --primary-dark: #2478c7;

    --cyan: #35d9ff;
    --green: #4ade80;
    --yellow: #fbbf24;
    --red: #fb7185;

    --shadow:
        0 25px 70px rgba(0, 0, 0, 0.35);
}


/* ---------------------------------------------------------
   GLOBAL
--------------------------------------------------------- */

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    scroll-behavior: smooth;
    -webkit-font-smoothing: antialiased;
}

body {
    font-family: 'Inter', sans-serif;
    color: var(--text);
    min-height: 100vh;
    background:
        radial-gradient(
            circle at 15% 5%,
            rgba(45, 140, 255, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 85% 15%,
            rgba(95, 80, 255, 0.14),
            transparent 28%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(0, 200, 255, 0.08),
            transparent 35%
        ),
        var(--bg);

    background-attachment: fixed;
    overflow-x: hidden;
}


/* AI GRID BACKGROUND */

body::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;

    background-image:
        linear-gradient(
            rgba(100, 170, 255, 0.045) 1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            rgba(100, 170, 255, 0.045) 1px,
            transparent 1px
        );

    background-size: 44px 44px;

    mask-image:
        linear-gradient(
            to bottom,
            black 0%,
            rgba(0,0,0,0.5) 60%,
            transparent 100%
        );

    z-index: -2;
}


/* BLUE AI GLOW */

body::after {
    content: "";
    position: fixed;

    width: 500px;
    height: 500px;

    top: -250px;
    right: -180px;

    background: rgba(77, 163, 255, 0.10);
    filter: blur(100px);
    border-radius: 50%;

    pointer-events: none;
    z-index: -1;
}


button,
input {
    font-family: inherit;
}


/* ---------------------------------------------------------
   MAIN CONTAINER
--------------------------------------------------------- */

.container {
    width: min(920px, calc(100% - 36px));
    margin: 0 auto;
    padding-bottom: 80px;
}


/* ---------------------------------------------------------
   SCREEN SYSTEM
--------------------------------------------------------- */

.screen {
    display: none;
}

.screen.active {
    display: block;
    animation: fadeIn 0.35s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}


/* ---------------------------------------------------------
   NAVBAR
--------------------------------------------------------- */

nav {
    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 22px 0;

    border-bottom: 1px solid var(--border);

    margin-bottom: 55px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}


/* AI LOGO */

.brand .seal {
    width: 42px;
    height: 42px;

    border-radius: 12px;

    display: flex;
    align-items: center;
    justify-content: center;

    font-family: 'Space Grotesk', sans-serif;
    font-size: 18px;
    font-weight: 700;

    color: white;

    background:
        linear-gradient(
            135deg,
            #2478c7,
            #35d9ff
        );

    box-shadow:
        0 0 25px rgba(53, 217, 255, 0.22);

    position: relative;
}

.brand .seal::after {
    content: "";
    position: absolute;
    inset: -4px;

    border-radius: 15px;

    border: 1px solid rgba(77, 163, 255, 0.20);
}


/* BRAND NAME */

.brand .name {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 19px;
    letter-spacing: -0.02em;
}

.brand .name em {
    font-style: normal;
    color: var(--primary-light);
}

.brand .tagline {
    margin-top: 2px;

    font-size: 9px;
    letter-spacing: 0.16em;

    text-transform: uppercase;

    color: var(--text-muted);
}


/* NAV BUTTON */

.nav-link {
    background: rgba(77, 163, 255, 0.07);

    border: 1px solid var(--border);

    color: var(--text-soft);

    padding: 9px 14px;

    border-radius: 8px;

    font-size: 11px;
    font-weight: 600;

    letter-spacing: 0.05em;
    text-transform: uppercase;

    cursor: pointer;

    transition: 0.2s ease;
}

.nav-link:hover {
    border-color: var(--border-bright);
    color: var(--text);
    background: rgba(77, 163, 255, 0.12);
}


/* NAV ACTIONS CONTAINER */

.nav-actions {
    display: flex;
    align-items: center;
    gap: 12px;
}


/* SIGN IN BUTTON */

.btn-signin {
    background: transparent;
    border: 1.5px solid var(--primary-light);
    color: var(--primary-light);
    padding: 10px 18px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 0 15px rgba(112, 187, 255, 0.15);
}

.btn-signin:hover {
    background: rgba(112, 187, 255, 0.10);
    border-color: var(--cyan);
    color: var(--cyan);
    transform: translateY(-1px);
    box-shadow: 0 0 20px rgba(112, 187, 255, 0.25);
}

.btn-signin:active {
    transform: translateY(0);
}


/* LOG IN BUTTON */

.btn-login {
    background: linear-gradient(135deg, var(--primary-dark), var(--primary));
    border: none;
    color: white;
    padding: 10px 18px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 6px 20px rgba(77, 163, 255, 0.25);
}

.btn-login:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(77, 163, 255, 0.35);
}

.btn-login:active {
    transform: translateY(0);
}


/* ---------------------------------------------------------
   AUTHENTICATION
--------------------------------------------------------- */

.auth-container {
    max-width: 420px;
    margin: 60px auto;
}

.auth-header {
    text-align: center;
    margin-bottom: 40px;
}

.auth-header .section-title {
    margin-bottom: 10px;
    background: linear-gradient(90deg, var(--primary-light), var(--cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.auth-form {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.form-group label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-soft);
}

.form-group input {
    background: rgba(13, 29, 48, 0.6);
    border: 1.5px solid var(--border);
    color: var(--text);
    padding: 12px 15px;
    border-radius: 9px;
    font-size: 14px;
    transition: all 0.3s ease;
    outline: none;
}

.form-group input::placeholder {
    color: var(--text-muted);
}

.form-group input:focus {
    border-color: var(--primary-light);
    background: rgba(13, 29, 48, 0.8);
    box-shadow: 0 0 15px rgba(112, 187, 255, 0.15);
}

.form-group input:hover {
    border-color: rgba(112, 187, 255, 0.3);
}

.auth-divider {
    text-align: center;
    margin: 20px 0;
    position: relative;
    color: var(--text-muted);
    font-size: 12px;
}

.auth-divider::before,
.auth-divider::after {
    content: "";
    position: absolute;
    top: 50%;
    width: 45%;
    height: 1px;
    background: var(--border);
}

.auth-divider::before {
    left: 0;
}

.auth-divider::after {
    right: 0;
}

.auth-footer {
    text-align: center;
    color: var(--text-soft);
    font-size: 13px;
    margin-top: 15px;
}

.link-btn {
    background: none;
    border: none;
    color: var(--primary-light);
    font-weight: 700;
    cursor: pointer;
    padding: 0;
    margin-left: 5px;
    text-decoration: underline;
    transition: all 0.2s ease;
}

.link-btn:hover {
    color: var(--cyan);
}


/* ---------------------------------------------------------
   HERO
--------------------------------------------------------- */

.hero {
    padding: 25px 0 50px;

    max-width: 760px;
}

.eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;

    font-size: 11px;
    font-weight: 600;

    letter-spacing: 0.12em;
    text-transform: uppercase;

    color: var(--primary-light);

    margin-bottom: 18px;
}

.eyebrow::before {
    content: "";

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: var(--cyan);

    box-shadow:
        0 0 12px var(--cyan);
}

.hero h1 {
    font-family: 'Space Grotesk', sans-serif;

    font-size: clamp(36px, 6vw, 62px);

    line-height: 1.04;

    letter-spacing: -0.045em;

    max-width: 760px;

    margin-bottom: 20px;
}

.hero h1 span {
    background:
        linear-gradient(
            90deg,
            var(--primary-light),
            var(--cyan)
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    color: var(--text-soft);

    font-size: 16px;

    line-height: 1.7;

    max-width: 650px;

    margin-bottom: 30px;
}


/* ---------------------------------------------------------
   BUTTON
--------------------------------------------------------- */

.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 9px;

    border: none;

    background:
        linear-gradient(
            135deg,
            var(--primary-dark),
            var(--primary)
        );

    color: white;

    padding: 13px 22px;

    border-radius: 9px;

    font-size: 12px;
    font-weight: 700;

    letter-spacing: 0.05em;
    text-transform: uppercase;

    cursor: pointer;

    box-shadow:
        0 8px 25px rgba(77, 163, 255, 0.18);

    transition:
        transform 0.18s ease,
        box-shadow 0.18s ease;
}

.btn:hover {
    transform: translateY(-2px);

    box-shadow:
        0 12px 32px rgba(77, 163, 255, 0.28);
}

.btn:active {
    transform: translateY(0);
}

.btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    transform: none;
}

.btn-block {
    width: 100%;
}

.btn-secondary {
    background: transparent;

    border: 1px solid var(--border-bright);

    color: var(--primary-light);

    box-shadow: none;
}

.btn-secondary:hover {
    background: rgba(77, 163, 255, 0.08);
}


/* ---------------------------------------------------------
   FEATURE CARDS
--------------------------------------------------------- */

.feature-grid {
    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 14px;

    margin-bottom: 30px;
}

.feature {
    background: rgba(13, 29, 48, 0.55);

    border: 1px solid var(--border);

    border-radius: 13px;

    padding: 20px;

    transition: 0.2s ease;
}

.feature:hover {
    transform: translateY(-3px);

    border-color: var(--border-bright);

    background: var(--card-hover);
}

.feature-icon {
    width: 38px;
    height: 38px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 10px;

    background: rgba(77, 163, 255, 0.10);

    color: var(--primary-light);

    font-size: 18px;

    margin-bottom: 14px;
}

.feature h4 {
    font-family: 'Space Grotesk', sans-serif;

    font-size: 14px;

    margin-bottom: 7px;
}

.feature p {
    color: var(--text-muted);

    font-size: 12px;

    line-height: 1.55;
}


/* ---------------------------------------------------------
   CARDS
--------------------------------------------------------- */

.card {
    background:
        linear-gradient(
            145deg,
            rgba(18, 38, 62, 0.88),
            rgba(8, 22, 37, 0.88)
        );

    border: 1px solid var(--border);

    border-radius: 14px;

    padding: 22px;

    margin-bottom: 15px;

    box-shadow: var(--shadow);

    backdrop-filter: blur(14px);

    position: relative;

    overflow: hidden;
}

.card::before {
    content: "";

    position: absolute;

    top: 0;
    left: 0;
    right: 0;

    height: 1px;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(100, 190, 255, 0.35),
            transparent
        );
}

.card h3 {
    font-family: 'Space Grotesk', sans-serif;

    font-size: 12px;

    letter-spacing: 0.08em;

    text-transform: uppercase;

    color: var(--text-soft);

    margin-bottom: 15px;
}


/* ---------------------------------------------------------
   SECTION HEADINGS
--------------------------------------------------------- */

.section-title {
    font-family: 'Space Grotesk', sans-serif;

    font-size: 28px;

    font-weight: 700;

    letter-spacing: -0.025em;

    margin-bottom: 7px;
}

.section-sub {
    font-size: 11px;

    color: var(--text-muted);

    letter-spacing: 0.08em;

    text-transform: uppercase;

    margin-bottom: 25px;
}


/* ---------------------------------------------------------
   UPLOAD AREA
--------------------------------------------------------- */

.dropzone {
    border: 1px dashed rgba(100, 180, 255, 0.35);

    border-radius: 14px;

    padding: 65px 25px;

    text-align: center;

    cursor: pointer;

    background:
        radial-gradient(
            circle at center,
            rgba(77, 163, 255, 0.08),
            transparent 60%
        ),
        rgba(10, 26, 43, 0.7);

    transition:
        border-color 0.2s ease,
        background 0.2s ease,
        transform 0.2s ease;
}

.dropzone:hover {
    border-color: var(--primary);

    background:
        radial-gradient(
            circle at center,
            rgba(77, 163, 255, 0.13),
            transparent 60%
        ),
        rgba(10, 26, 43, 0.9);

    transform: translateY(-2px);
}

.dropzone.dragover {
    border-color: var(--cyan);

    background:
        rgba(53, 217, 255, 0.10);
}

.dropzone svg {
    width: 52px;
    height: 52px;

    margin-bottom: 17px;

    stroke: var(--primary-light);

    filter:
        drop-shadow(
            0 0 12px rgba(77, 163, 255, 0.3)
        );
}

.dropzone p {
    color: var(--text);

    font-size: 15px;

    font-weight: 600;

    margin-bottom: 7px;
}

.dropzone .sub {
    font-size: 10px;

    color: var(--text-muted);

    letter-spacing: 0.08em;
}

#fileInput {
    display: none;
}

#fileNameLabel {
    margin-top: 18px;

    min-height: 20px;

    color: var(--cyan);

    font-size: 12px;

    font-weight: 600;
}


/* ---------------------------------------------------------
   PROCESSING
--------------------------------------------------------- */

.processing-wrap {
    padding: 70px 0;

    text-align: center;
}

.processing-wrap h1 {
    font-family: 'Space Grotesk', sans-serif;

    font-size: 28px;

    margin-bottom: 8px;
}

.processing-wrap .section-sub {
    text-align: center;
}


/* AI PROCESSING ORB */

.ai-orb {
    width: 90px;
    height: 90px;

    margin: 0 auto 28px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle at 35% 30%,
            #b7e6ff,
            #4da3ff 35%,
            #1a5da0 70%,
            #0a2038
        );

    box-shadow:
        0 0 25px rgba(77, 163, 255, 0.35),
        0 0 80px rgba(53, 217, 255, 0.12);

    animation: pulseOrb 1.8s ease-in-out infinite;
}

@keyframes pulseOrb {

    0%,
    100% {
        transform: scale(0.92);

        box-shadow:
            0 0 25px rgba(77, 163, 255, 0.3),
            0 0 70px rgba(53, 217, 255, 0.08);
    }

    50% {
        transform: scale(1.04);

        box-shadow:
            0 0 35px rgba(77, 163, 255, 0.5),
            0 0 100px rgba(53, 217, 255, 0.15);
    }
}


/* CHECKLIST */

.checklist {
    list-style: none;

    margin: 30px auto 0;

    max-width: 430px;

    text-align: left;
}

.checklist li {
    display: flex;

    align-items: center;

    gap: 13px;

    padding: 14px 0;

    color: var(--text-muted);

    font-size: 13px;

    border-bottom: 1px solid rgba(100, 180, 255, 0.08);

    transition: 0.2s ease;
}

.checklist li:last-child {
    border-bottom: none;
}

.checklist li.active {
    color: var(--primary-light);
}

.checklist li.done {
    color: var(--green);
}

.checklist li .box {
    width: 20px;
    height: 20px;

    border-radius: 6px;

    border: 1px solid rgba(100, 180, 255, 0.25);

    flex-shrink: 0;

    display: flex;

    align-items: center;

    justify-content: center;

    transition: 0.2s ease;
}

.checklist li.active .box {
    border-color: var(--primary);

    box-shadow:
        0 0 12px rgba(77, 163, 255, 0.25);
}

.checklist li.done .box {
    border-color: var(--green);

    background: rgba(74, 222, 128, 0.10);

    color: var(--green);
}

.checklist li.done .box::after {
    content: "✓";
}


/* ---------------------------------------------------------
   RESULT PAGE
--------------------------------------------------------- */

.ref-code {
    color: var(--text-muted);

    font-size: 10px;

    letter-spacing: 0.08em;

    margin-bottom: 17px;
}

.doc-card {
    padding: 26px;

    overflow: hidden;
}


/* AI VERIFIED BADGE */

.stamp {
    position: absolute;

    top: 18px;
    right: 18px;

    width: 105px;
    height: 105px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    color: var(--cyan);

    border: 1px solid rgba(53, 217, 255, 0.55);

    background:
        rgba(53, 217, 255, 0.05);

    transform:
        rotate(-8deg)
        scale(0.5);

    opacity: 0;

    transition:
        transform 0.45s cubic-bezier(.2,1.4,.4,1),
        opacity 0.3s ease;

    pointer-events: none;

    box-shadow:
        0 0 25px rgba(53, 217, 255, 0.10);
}

.stamp.show {
    transform:
        rotate(-8deg)
        scale(1);

    opacity: 0.9;
}

.stamp-inner {
    text-align: center;

    font-size: 8px;

    font-weight: 700;

    letter-spacing: 0.1em;
}

.stamp-inner strong {
    display: block;

    font-family: 'Space Grotesk', sans-serif;

    font-size: 17px;

    margin-bottom: 3px;
}


/* RESULT FIELDS */

.field-row {
    display: flex;

    gap: 14px;

    padding: 16px 0;

    border-bottom: 1px solid rgba(100, 180, 255, 0.09);
}

.field-row:last-child {
    border-bottom: none;
}

.field-row .icon {
    width: 22px;

    flex-shrink: 0;

    margin-top: 2px;
}

.field-row .icon svg {
    width: 19px;
    height: 19px;

    stroke: var(--primary-light);

    fill: none;
}

.field-row .label {
    color: var(--text-muted);

    font-size: 9px;

    font-weight: 700;

    text-transform: uppercase;

    letter-spacing: 0.1em;

    margin-bottom: 5px;
}

.field-row .value {
    color: var(--text);

    font-size: 14px;

    line-height: 1.55;
}

.field-row ul {
    padding-left: 18px;

    margin-top: 4px;
}


/* ---------------------------------------------------------
   BADGES
--------------------------------------------------------- */

.badge {
    display: inline-flex;

    align-items: center;

    padding: 4px 9px;

    border-radius: 20px;

    font-size: 9px;

    font-weight: 700;

    letter-spacing: 0.07em;

    text-transform: uppercase;

    border: 1px solid;
}

.badge.urgent {
    color: var(--red);

    border-color: rgba(251, 113, 133, 0.4);

    background: rgba(251, 113, 133, 0.08);
}

.badge.important {
    color: var(--yellow);

    border-color: rgba(251, 191, 36, 0.35);

    background: rgba(251, 191, 36, 0.08);
}

.badge.normal {
    color: var(--green);

    border-color: rgba(74, 222, 128, 0.35);

    background: rgba(74, 222, 128, 0.08);
}


/* ---------------------------------------------------------
   NOTICE LIST
--------------------------------------------------------- */

.notice-card {
    cursor: pointer;

    transition:
        transform 0.18s ease,
        border-color 0.18s ease;
}

.notice-card:hover {
    transform: translateY(-2px);

    border-color: var(--border-bright);
}

.notice-card .top {
    display: flex;

    justify-content: space-between;

    align-items: flex-start;

    gap: 12px;

    margin-bottom: 8px;
}

.notice-card h4 {
    font-family: 'Space Grotesk', sans-serif;

    font-size: 15px;

    font-weight: 600;
}

.notice-card .meta {
    color: var(--text-muted);

    font-size: 10px;

    letter-spacing: 0.04em;
}


/* ---------------------------------------------------------
   ERROR
--------------------------------------------------------- */

.error-box {
    background: rgba(251, 113, 133, 0.08);

    border: 1px solid rgba(251, 113, 133, 0.45);

    color: #ff9aaa;

    border-radius: 10px;

    padding: 15px 17px;

    font-size: 12px;

    margin-top: 16px;

    line-height: 1.6;
}


/* ---------------------------------------------------------
   EMPTY STATE
--------------------------------------------------------- */

.empty-state {
    text-align: center;

    color: var(--text-muted);

    padding: 35px 0;

    font-size: 12px;
}


/* ---------------------------------------------------------
   SPACING
--------------------------------------------------------- */

.spacer {
    height: 15px;
}


/* ---------------------------------------------------------
   FOOTER
--------------------------------------------------------- */

.footer {
    margin-top: 50px;

    padding-top: 20px;

    border-top: 1px solid var(--border);

    text-align: center;

    color: var(--text-muted);

    font-size: 10px;

    letter-spacing: 0.05em;
}


/* ---------------------------------------------------------
   RESPONSIVE
--------------------------------------------------------- */

@media (max-width: 700px) {

    .container {
        width: min(100% - 26px, 920px);
    }

    nav {
        margin-bottom: 35px;
        flex-wrap: wrap;
    }

    .nav-actions {
        width: 100%;
        gap: 8px;
        margin-top: 12px;
    }

    .btn-signin,
    .btn-login {
        flex: 1;
        padding: 10px 12px;
        font-size: 11px;
    }

    .hero h1 {
        font-size: 38px;
    }

    .feature-grid {
        grid-template-columns: 1fr;
    }

    .stamp {
        width: 82px;
        height: 82px;

        top: 15px;
        right: 12px;
    }

    .doc-card {
        padding: 21px;
    }

    .auth-container {
        max-width: 100%;
        margin: 30px 0;
    }

    .auth-header {
        margin-bottom: 30px;
    }

    .auth-header .section-title {
        font-size: 24px;
    }

    .auth-form {
        gap: 16px;
    }

    .form-group label {
        font-size: 11px;
    }

    .form-group input {
        padding: 11px 12px;
        font-size: 13px;
    }
}

</style>
</head>


<body>

<div class="container">

    <!-- =====================================================
         NAVIGATION
    ====================================================== -->

    <nav>

        <div class="brand">

            <div class="seal">
                N
            </div>

            <div>

                <div class="name">
                    Notice<em>Sense</em> AI
                </div>

                <div class="tagline">
                    AI-powered notice intelligence
                </div>

            </div>

        </div>


        <div class="nav-actions">

            <button
                class="nav-link"
                onclick="showScreen('dashboard')">

                My Notices

            </button>

            <button
                class="btn-signin"
                onclick="showScreen('signin')">

                Sign In

            </button>

            <button
                class="btn-login"
                onclick="showScreen('login')">

                Log In

            </button>

        </div>

    </nav>


    <!-- =====================================================
         HOME
    ====================================================== -->

    <section
        id="screen-home"
        class="screen active">

        <div class="hero">

            <div class="eyebrow">
                AI Notice Intelligence
            </div>

            <h1>
                Turn complex notices into
                <span>clear actions.</span>
            </h1>

            <p>
                Upload a college notice and let AI understand
                the important information — deadlines,
                target audience, required actions, documents,
                locations and more.
            </p>

            <button
                class="btn"
                onclick="showScreen('upload')">

                Analyze a Notice

            </button>

        </div>


        <!-- FEATURES -->

        <div class="feature-grid">

            <div class="feature">

                <div class="feature-icon">
                    📄
                </div>

                <h4>
                    Understand
                </h4>

                <p>
                    AI analyzes the content of your notice
                    and understands its meaning.
                </p>

            </div>


            <div class="feature">

                <div class="feature-icon">
                    🧠
                </div>

                <h4>
                    Extract
                </h4>

                <p>
                    Important dates, instructions,
                    audience and other information are extracted.
                </p>

            </div>


            <div class="feature">

                <div class="feature-icon">
                    ⚡
                </div>

                <h4>
                    Simplify
                </h4>

                <p>
                    Get a clear and structured summary
                    instead of reading the entire notice.
                </p>

            </div>

        </div>


        <!-- RECENT -->

        <div class="card">

            <h3>
                Recently Analyzed
            </h3>

            <div
                id="homeRecentList"
                class="empty-state">

                No notices analyzed yet.

            </div>

        </div>

    </section>


    <!-- =====================================================
         SIGN IN
    ====================================================== -->

    <section
        id="screen-signin"
        class="screen">

        <div class="auth-container">

            <div class="auth-header">

                <h2 class="section-title">
                    Create Account
                </h2>

                <div class="section-sub">
                    Join NoticeSense AI to get started
                </div>

            </div>


            <form class="auth-form" id="signupForm">

                <div class="form-group">

                    <label for="signupEmail">Email Address</label>

                    <input
                        type="email"
                        id="signupEmail"
                        placeholder="you@example.com"
                        required>

                </div>


                <div class="form-group">

                    <label for="signupPassword">Password</label>

                    <input
                        type="password"
                        id="signupPassword"
                        placeholder="At least 8 characters"
                        required>

                </div>


                <div class="form-group">

                    <label for="signupConfirm">Confirm Password</label>

                    <input
                        type="password"
                        id="signupConfirm"
                        placeholder="Confirm your password"
                        required>

                </div>


                <button
                    type="submit"
                    class="btn btn-block">

                    Create Account

                </button>

            </form>


            <div class="auth-divider">
                or
            </div>


            <div class="auth-footer">

                Already have an account?

                <button
                    class="link-btn"
                    onclick="showScreen('login')">

                    Log In

                </button>

            </div>

        </div>

    </section>


    <!-- =====================================================
         LOG IN
    ====================================================== -->

    <section
        id="screen-login"
        class="screen">

        <div class="auth-container">

            <div class="auth-header">

                <h2 class="section-title">
                    Welcome Back
                </h2>

                <div class="section-sub">
                    Log in to access your notices
                </div>

            </div>


            <form class="auth-form" id="loginForm">

                <div class="form-group">

                    <label for="loginEmail">Email Address</label>

                    <input
                        type="email"
                        id="loginEmail"
                        placeholder="you@example.com"
                        required>

                </div>


                <div class="form-group">

                    <label for="loginPassword">Password</label>

                    <input
                        type="password"
                        id="loginPassword"
                        placeholder="Enter your password"
                        required>

                </div>


                <button
                    type="submit"
                    class="btn btn-block">

                    Log In

                </button>

            </form>


            <div class="auth-divider">
                or
            </div>


            <div class="auth-footer">

                Don't have an account?

                <button
                    class="link-btn"
                    onclick="showScreen('signin')">

                    Sign Up

                </button>

            </div>

        </div>

    </section>


    <!-- =====================================================
         UPLOAD
    ====================================================== -->

    <section
        id="screen-upload"
        class="screen">

        <h2 class="section-title">
            Analyze Your Notice
        </h2>

        <div class="section-sub">
            Upload a document for AI analysis
        </div>


        <div
            class="dropzone"
            id="dropzone"
            onclick="document.getElementById('fileInput').click()">

            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke-width="1.4"
                stroke-linecap="round"
                stroke-linejoin="round">

                <path d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/>

                <path d="M12 3v11"/>

                <path d="M7 8l5-5 5 5"/>

            </svg>


            <p>
                Drop your notice here
            </p>

            <div class="sub">
                or click to browse
            </div>

            <div class="sub" style="margin-top:10px;">
                PDF · JPG · PNG
            </div>


            <div id="fileNameLabel"></div>

        </div>


        <input
            type="file"
            id="fileInput"
            accept=".pdf,.jpg,.jpeg,.png"
        />


        <div class="spacer"></div>


        <button
            class="btn btn-block"
            id="analyzeBtn"
            onclick="startAnalysis()"
            disabled>

            Analyze With AI

        </button>

    </section>


    <!-- =====================================================
         PROCESSING
    ====================================================== -->

    <section
        id="screen-processing"
        class="screen">

        <div class="processing-wrap">

            <div class="ai-orb"></div>


            <div class="eyebrow">
                AI Processing
            </div>


            <h1>
                Understanding your notice…
            </h1>


            <div class="section-sub">
                NoticeSense AI is analyzing the document
            </div>


            <ul
                class="checklist"
                id="checklist">

                <li data-step="0">

                    <span class="box"></span>

                    Reading document

                </li>


                <li data-step="1">

                    <span class="box"></span>

                    Understanding content

                </li>


                <li data-step="2">

                    <span class="box"></span>

                    Extracting important information

                </li>


                <li data-step="3">

                    <span class="box"></span>

                    Creating summary

                </li>

            </ul>

        </div>

    </section>


    <!-- =====================================================
         RESULT
    ====================================================== -->

    <section
        id="screen-result"
        class="screen">

        <h2
            class="section-title"
            id="resultTitle">

            Notice Analysis

        </h2>


        <div
            class="ref-code"
            id="resultRef">
        </div>


        <div
            class="card doc-card"
            id="resultCardWrap">


            <!-- AI VERIFIED STAMP -->

            <div
                class="stamp"
                id="stampMark">

                <div class="stamp-inner">

                    <strong>AI</strong>

                    VERIFIED

                    <br>

                    BY

                    <br>

                    NOTICESENSE

                </div>

            </div>


            <div id="resultFields"></div>

        </div>


        <div id="resultError"></div>


        <div class="spacer"></div>


        <button
            class="btn btn-secondary btn-block"
            onclick="showScreen('upload'); resetUpload();">

            Analyze Another Notice

        </button>

    </section>


    <!-- =====================================================
         DASHBOARD
    ====================================================== -->

    <section
        id="screen-dashboard"
        class="screen">

        <h2 class="section-title">
            My Notices
        </h2>

        <div class="section-sub">
            Your analyzed notices
        </div>


        <div
            id="dashboardList"
            class="empty-state">

            No notices yet.

            <br><br>

            Analyze your first notice to get started.

        </div>

    </section>


    <!-- FOOTER -->

    <div class="footer">

        NoticeSense AI · Intelligent Notice Understanding

    </div>

</div>


<script>

let selectedFile = null;

let lastNoticeId = null;


/* =========================================================
   SCREEN NAVIGATION
========================================================= */

function showScreen(id) {

    document
        .querySelectorAll('.screen')
        .forEach(screen => {

            screen.classList.remove('active');

        });


    const target =
        document.getElementById('screen-' + id);


    if (target) {

        target.classList.add('active');

    }


    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });


    if (id === 'dashboard') {

        refreshNoticeList('dashboardList');

    }


    if (id === 'home') {

        refreshNoticeList('homeRecentList');

    }

}


/* =========================================================
   RESET UPLOAD
========================================================= */

function resetUpload() {

    selectedFile = null;

    document.getElementById('fileInput').value = '';

    document.getElementById('fileNameLabel').textContent = '';

    document.getElementById('analyzeBtn').disabled = true;

    document
        .getElementById('stampMark')
        .classList.remove('show');

}


/* =========================================================
   AUTHENTICATION FORMS
========================================================= */

// Sign Up Form Handler
const signupForm = document.getElementById('signupForm');
if (signupForm) {
    signupForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const email = document.getElementById('signupEmail').value;
        const password = document.getElementById('signupPassword').value;
        const confirm = document.getElementById('signupConfirm').value;

        if (password !== confirm) {
            alert('Passwords do not match!');
            return;
        }

        if (password.length < 8) {
            alert('Password must be at least 8 characters!');
            return;
        }

        // Here you would send data to your backend
        console.log('Signup:', { email, password });
        alert('Account created successfully! Please log in.');
        
        // Clear form and navigate to login
        signupForm.reset();
        showScreen('login');
    });
}

// Login Form Handler
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;

        // Here you would send data to your backend
        console.log('Login:', { email, password });
        alert('Logged in successfully!');
        
        // Clear form and navigate to home
        loginForm.reset();
        showScreen('home');
    });
}


/* =========================================================
   FILE UPLOAD
========================================================= */

const dropzone =
    document.getElementById('dropzone');

const fileInput =
    document.getElementById('fileInput');


fileInput.addEventListener(
    'change',
    (event) => {

        if (event.target.files.length) {

            handleFile(event.target.files[0]);

        }

    }
);


/* DRAG EVENTS */

['dragover', 'dragenter'].forEach(
    eventName => {

        dropzone.addEventListener(
            eventName,
            event => {

                event.preventDefault();

                dropzone.classList.add('dragover');

            }
        );

    }
);


['dragleave', 'drop'].forEach(
    eventName => {

        dropzone.addEventListener(
            eventName,
            event => {

                event.preventDefault();

                dropzone.classList.remove('dragover');

            }
        );

    }
);


dropzone.addEventListener(
    'drop',
    event => {

        if (event.dataTransfer.files.length) {

            handleFile(
                event.dataTransfer.files[0]
            );

        }

    }
);


/* HANDLE FILE */

function handleFile(file) {

    const allowedTypes = [
        'application/pdf',
        'image/jpeg',
        'image/png'
    ];


    if (
        !allowedTypes.includes(file.type)
    ) {

        alert(
            'Please upload a PDF, JPG or PNG file.'
        );

        return;

    }


    selectedFile = file;


    document
        .getElementById('fileNameLabel')
        .textContent =
        '✓ ' + file.name;


    document
        .getElementById('analyzeBtn')
        .disabled = false;

}


/* =========================================================
   START ANALYSIS
========================================================= */

async function startAnalysis() {

    if (!selectedFile) {

        return;

    }


    showScreen('processing');

    animateChecklist();


    const formData =
        new FormData();


    formData.append(
        'file',
        selectedFile
    );


    try {

        const response =
            await fetch(
                '/analyze',
                {
                    method: 'POST',
                    body: formData
                }
            );


        const data =
            await response.json();


        setTimeout(
            () => {

                renderResult(
                    data,
                    response.ok
                );

            },
            1600
        );


    } catch (error) {

        setTimeout(
            () => {

                renderResult(
                    {
                        error:
                            'Network error: ' +
                            error.message
                    },
                    false
                );

            },
            1600
        );

    }

}


/* =========================================================
   PROCESSING ANIMATION
========================================================= */

function animateChecklist() {

    const items =
        document.querySelectorAll(
            '#checklist li'
        );


    items.forEach(item => {

        item.classList.remove(
            'done',
            'active'
        );

    });


    let index = 0;


    const interval =
        setInterval(() => {


            if (index > 0) {

                items[index - 1]
                    .classList.add('done');

            }


            if (index < items.length) {

                items[index]
                    .classList.add('active');

            } else {

                clearInterval(interval);

            }


            index++;

        }, 380);

}


/* =========================================================
   REFERENCE CODE
========================================================= */

function refCode(id) {

    const year =
        new Date().getFullYear();


    const short =
        (id || '')
            .replace(/-/g, '')
            .slice(0, 6)
            .toUpperCase();


    return `REF NS-${year}-${short || '000000'}`;

}


/* =========================================================
   RENDER AI RESULT
========================================================= */

function renderResult(data, ok) {

    const errorBox =
        document.getElementById(
            'resultError'
        );


    const fieldsBox =
        document.getElementById(
            'resultFields'
        );


    const titleBox =
        document.getElementById(
            'resultTitle'
        );


    const refBox =
        document.getElementById(
            'resultRef'
        );


    const stamp =
        document.getElementById(
            'stampMark'
        );


    fieldsBox.innerHTML = '';

    errorBox.innerHTML = '';

    refBox.textContent = '';

    stamp.classList.remove('show');


    /* ERROR */

    if (!ok || data.error) {

        titleBox.textContent =
            'Analysis Failed';


        errorBox.innerHTML =
            `
            <div class="error-box">
                ${escapeHtml(
                    data.error ||
                    'Unknown error'
                )}
            </div>
            `;


        showScreen('result');

        return;

    }


    lastNoticeId =
        data.id;


    const fields =
        data.data || {};


    titleBox.textContent =
        fields.Title ||
        fields.NoticeType ||
        'Notice';


    refBox.textContent =
        refCode(data.id);


    /* RESULT FIELDS */

    const rows = [

        [
            'audience',
            'Target Audience',
            fields.TargetAudience
        ],

        [
            'calendar',
            'Deadline',
            fields.Deadline
        ],

        [
            'clock',
            'Time',
            fields.Time
        ],

        [
            'pin',
            'Location',
            fields.Location
        ],

        [
            'flag',
            'Action Required',
            fields.Instructions
        ],

        [
            'paperclip',
            'Required Documents',
            fields.RequiredDocuments
        ],

        [
            'phone',
            'Contact',
            fields.ContactInformation
        ]

    ];


    rows.forEach(
        ([icon, label, value]) => {


            if (
                !value ||
                (
                    Array.isArray(value) &&
                    value.length === 0
                )
            ) {

                return;

            }


            const valueHtml =
                Array.isArray(value)

                    ? '<ul>' +
                      value
                        .map(
                            item =>
                                `<li>${escapeHtml(item)}</li>`
                        )
                        .join('') +
                      '</ul>'

                    : escapeHtml(value);


            fieldsBox.innerHTML +=
                `
                <div class="field-row">

                    <div class="icon">
                        ${fieldIcon(icon)}
                    </div>

                    <div>

                        <div class="label">
                            ${label}
                        </div>

                        <div class="value">
                            ${valueHtml}
                        </div>

                    </div>

                </div>
                `;

        }
    );


    showScreen('result');


    requestAnimationFrame(
        () => {

            setTimeout(
                () => {

                    stamp.classList.add(
                        'show'
                    );

                },
                120
            );

        }
    );

}


/* =========================================================
   FIELD ICONS
========================================================= */

function fieldIcon(name) {

    const icons = {

        audience:
            `
            <circle
                cx="9"
                cy="7"
                r="3"
            />

            <path
                d="M2 20c0-4 3-6 7-6s7 2 7 6"
            />

            <path
                d="M16 8a3 3 0 0 1 0 6"
            />

            <path
                d="M18.5 14.5c2 .5 3.5 2 3.5 5.5"
            />
            `,


        calendar:
            `
            <rect
                x="3"
                y="5"
                width="18"
                height="16"
                rx="1"
            />

            <path d="M3 10h18"/>

            <path d="M8 3v4"/>

            <path d="M16 3v4"/>
            `,


        clock:
            `
            <circle
                cx="12"
                cy="12"
                r="9"
            />

            <path
                d="M12 7v5l3 2"
            />
            `,


        pin:
            `
            <path
                d="M12 21s7-6.5 7-12a7 7 0 1 0-14 0c0 5.5 7 12 7 12z"
            />

            <circle
                cx="12"
                cy="9"
                r="2.3"
            />
            `,


        flag:
            `
            <path
                d="M5 3v18"
            />

            <path
                d="M5 4h11l-2.5 4L16 12H5"
            />
            `,


        paperclip:
            `
            <path
                d="M18 10 9.5 18.5a4 4 0 0 1-5.66-5.66L13 3.68A2.7 2.7 0 1 1 16.8 7.5L8 16.3"
            />
            `,


        phone:
            `
            <path
                d="M5 4h4l1.5 4.5L8 10.5a11 11 0 0 0 5.5 5.5l1.9-2.5 4.5 1.5v4a2 2 0 0 1-2.2 2A17 17 0 0 1 3 6.2 2 2 0 0 1 5 4z"
            />
            `

    };


    return `
        <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round">

            ${icons[name] || ''}

        </svg>
    `;

}


/* =========================================================
   NOTICE DASHBOARD
========================================================= */

async function refreshNoticeList(targetId) {

    const element =
        document.getElementById(
            targetId
        );


    try {

        const response =
            await fetch('/notices');


        const notices =
            await response.json();


        if (!notices.length) {

            element.className =
                'empty-state';

            element.innerHTML =
                'No notices yet.';

            return;

        }


        element.className = '';


        element.innerHTML =
            notices
                .map(
                    notice => {

                        const urgency =
                            classifyUrgency(
                                notice.data.Deadline
                            );


                        return `
                        <div
                            class="card notice-card">

                            <div class="top">

                                <h4>
                                    ${escapeHtml(
                                        notice.data.Title ||
                                        notice.data.NoticeType ||
                                        'Notice'
                                    )}
                                </h4>

                                <span
                                    class="badge ${urgency}">

                                    ${urgency}

                                </span>

                            </div>


                            <div class="meta">

                                ${escapeHtml(
                                    notice.data.Deadline ||
                                    'No deadline'
                                )}

                                ·

                                ${refCode(
                                    notice.id
                                )}

                            </div>

                        </div>
                        `;

                    }
                )
                .join('');


    } catch (error) {

        element.className =
            'empty-state';

        element.textContent =
            'Could not load notices.';

    }

}


/* =========================================================
   URGENCY
========================================================= */

function classifyUrgency(deadline) {

    if (!deadline) {

        return 'normal';

    }


    const parsed =
        Date.parse(deadline);


    if (isNaN(parsed)) {

        return 'normal';

    }


    const daysLeft =
        (
            parsed -
            Date.now()
        ) /
        (
            1000 *
            60 *
            60 *
            24
        );


    if (daysLeft <= 3) {

        return 'urgent';

    }


    if (daysLeft <= 10) {

        return 'important';

    }


    return 'normal';

}


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHtml(str) {

    if (
        str === undefined ||
        str === null
    ) {

        return '';

    }


    const div =
        document.createElement('div');


    div.textContent = str;


    return div.innerHTML;

}

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


@app.route("/analyze", methods=["POST"])
def analyze():

    """
    Accepts a file upload and runs it through
    the notice-processing pipeline.

    The Azure service is imported lazily so that
    the Flask frontend can still start even when
    Azure credentials are not configured.
    """

    if "file" not in request.files:
        return jsonify({
            "error": "No file uploaded."
        }), 400


    uploaded = request.files["file"]


    if uploaded.filename == "":
        return jsonify({
            "error": "Empty filename."
        }), 400


    file_bytes = uploaded.read()


    try:

        from services.notice_processor import process_notice

    except Exception as e:

        return jsonify({

            "error":
                f"Backend AI service is not configured yet "
                f"({e.__class__.__name__}: {e}). "
                f"Check with the backend teammate that "
                f"ENDPOINT/ANALYZER are set and Azure credentials "
                f"(DefaultAzureCredential) are available."

        }), 503


    try:

        notice_data = process_notice(file_bytes)

    except Exception as e:

        return jsonify({

            "error":
                f"Analysis failed: "
                f"{e.__class__.__name__}: {e}"

        }), 502


    notice_id =str(uuid.uuid4())


    NOTICES[notice_id] = {

        "data":
            notice_data,

        "filename":
            uploaded.filename,

        "created_at":
            datetime.utcnow().isoformat(),

    }


    return jsonify({

        "id":
            notice_id,

        "data":
            notice_data

    })


@app.route("/notices", methods=["GET"])
def list_notices():

    result = [

        {
            "id": notice_id,

            "data":
                notice["data"],

            "filename":
                notice["filename"],

            "created_at":
                notice["created_at"]

        }

        for notice_id, notice
        in sorted(
            NOTICES.items(),
            key=lambda item:
                item[1]["created_at"],
            reverse=True
        )

    ]


    return jsonify(result)


@app.route("/notices/<notice_id>", methods=["GET"])
def get_notice(notice_id):

    notice = NOTICES.get(notice_id)


    if not notice:

        return jsonify({

            "error":
                "Notice not found."

        }), 404


    return jsonify(notice)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )