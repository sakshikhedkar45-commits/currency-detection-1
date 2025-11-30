# app.py
import streamlit as st
from PIL import Image, ImageStat, ImageFilter
import io
import random
import pandas as pd
import base64
from datetime import datetime

st.set_page_config(page_title="Currency Verification — Demo", layout="wide",
                   initial_sidebar_state="expanded")

# -------------------------
# --- Small DB of models ---
# -------------------------
CURRENCY_DB = {
    "INR": {
        "name": "Indian Rupee (INR)",
        "denominations": {
            "10": ["Watermark", "Security thread", "Intaglio print", "Latent image"],
            "50": ["Watermark", "Security thread", "Optically variable ink", "Microprint"],
            "2000": ["Watermark", "Security thread", "See-through register", "Hologram"]
        }
    },
    "USD": {
        "name": "US Dollar (USD)",
        "denominations": {
            "1": ["Portrait watermark", "Raised printing", "Microprinting"],
            "20": ["Security thread", "Color-shifting ink", "Portrait watermark"],
            "100": ["3D Security ribbon", "Color-shifting bell", "Large portrait watermark"]
        }
    },
    "EUR": {
        "name": "Euro (EUR)",
        "denominations": {
            "5": ["Hologram", "Watermark", "Raised print"],
            "50": ["Security thread", "Hologram", "See-through number"],
            "200": ["Watermark", "Security thread", "EUR hologram"]
        }
    }
}

# -------------------------
# --- Utility functions ---
# -------------------------
def image_stats_summary(img: Image.Image):
    """Compute lightness / sharpness proxies used only for simulated checks."""
    try:
        gray = img.convert("L").resize((300, 300))
        stat = ImageStat.Stat(gray)
        mean = stat.mean[0]
        stddev = stat.stddev[0]
        # simple "sharpness" proxy: variance of Laplacian-ish by applying a filter
        lap = gray.filter(ImageFilter.FIND_EDGES)
        lap_stat = ImageStat.Stat(lap)
        lap_mean = lap_stat.mean[0]
        return {"brightness": mean, "contrast": stddev, "edge_mean": lap_mean}
    except Exception:
        return {"brightness": 0, "contrast": 0, "edge_mean": 0}


def simulated_analysis(img: Image.Image, currency_code: str, denom: str):
    """
    SAFE simulation only:
     - randomly decide Real/Fake but use image stats to vary probabilities
     - produce which checklist items appear present/missing (simulated)
    """
    stats = image_stats_summary(img)
    # heuristic: brighter + more edges => slightly more likely "features visible"
    score = (stats["brightness"] / 128.0) + (stats["edge_mean"] / 50.0)
    # base probability
    base_prob_real = 0.55
    prob_real = min(max(base_prob_real + (score - 1.0) * 0.15 + random.uniform(-0.12, 0.12), 0.02), 0.98)

    is_real_sim = random.random() < prob_real

    # choose features to "detect" from DB
    expected = CURRENCY_DB.get(currency_code, {}).get("denominations", {}).get(denom, [])
    observed = []
    missing = []
    for f in expected:
        # if real simulated, more expected features detected
        if is_real_sim:
            present = random.random() < 0.8
        else:
            present = random.random() < 0.25
        if present:
            observed.append(f)
        else:
            missing.append(f)

    # also add a few "extra suspicious signs" (simulated)
    suspicious_reasons = []
    if not is_real_sim:
        suspicious_reasons = random.sample([
            "Uneven edge alignment",
            "Blurred microprint",
            "Odd color tint",
            "Inconsistent portrait size",
            "Missing watermark shadow"
        ], k=random.randint(1, 2))

    return {
        "simulated_real": is_real_sim,
        "probability_real": prob_real,
        "expected_features": expected,
        "observed_features": observed,
        "missing_features": missing,
        "suspicious_reasons": suspicious_reasons,
        "stats": stats
    }


def generate_ai_explanation(sim_result, currency_str, denom):
    """
    Produce an AI-style explanation paragraph (simulated, deterministic text).
    This is NOT real forensic analysis — purely educational.
    """
    header = f"Interpretation for {currency_str} — {denom} (simulated):"
    if sim_result["simulated_real"]:
        tone = [
            "The scanned note shows multiple expected security features. ",
            "Overall the image matches reference patterns used for genuine notes. "
        ]
        details = []
        if sim_result["observed_features"]:
            details.append("Observed features: " + ", ".join(sim_result["observed_features"]) + ".")
        if sim_result["missing_features"]:
            details.append("Minor features not clearly visible: " + ", ".join(sim_result["missing_features"]) + ".")
        if sim_result["suspicious_reasons"]:
            details.append("Additional notes: " + "; ".join(sim_result["suspicious_reasons"]) + ".")
        p = " ".join(tone + details)
        p += f" (Simulated confidence: {sim_result['probability_real']*100:.0f}%)"
    else:
        tone = [
            "The scanned note shows several inconsistencies with the expected reference. ",
            "These discrepancies suggest the note could be a forgery or is damaged/poorly scanned. "
        ]
        details = []
        if sim_result["missing_features"]:
            details.append("Missing or unclear features: " + ", ".join(sim_result["missing_features"]) + ".")
        if sim_result["suspicious_reasons"]:
            details.append("Suspicious signs: " + "; ".join(sim_result["suspicious_reasons"]) + ".")
        p = " ".join(tone + details)
        p += f" (Simulated confidence that note is fake: {(1 - sim_result['probability_real'])*100:.0f}%)"

    # friendly AI-like closing suggestion
    closing = (
        " This is an educational simulation — for a definitive determination consult bank note experts "
        "or use certified bank/forensic equipment."
    )
    return header + "\n\n" + p + "\n\n" + closing


def pretty_bytes(b):
    for unit in ['B','KB','MB','GB']:
        if b < 1024.0:
            return f"{b:3.1f}{unit}"
        b /= 1024.0
    return f"{b:.1f}TB"


# -------------------------
# --- Header / Styling ---
# -------------------------
def local_css(css: str):
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

css = """
.header {
  background: linear-gradient(90deg,#0f172a,#0f3460);
  padding: 1rem 2rem;
  border-radius: 8px;
  color: white;
}
.brand {
  font-size: 22px;
  font-weight: 700;
}
.subtitle { color: #cbd5e1; margin-top: 4px; }
.card { background: white; padding: 12px; border-radius: 8px; box-shadow: 0 6px 18px rgba(2,6,23,0.08); }
.small { font-size:13px; color:#64748b }
"""
local_css(css)

st.markdown(
    """
    <div class="header">
      <div class="brand">💡 Currency Verify — Educational Demo</div>
      <div class="subtitle">Simulated verification UI — not a forensic tool.</div>
    </div>
    """, unsafe_allow_html=True
)

# -------------------------
# --- Sidebar Navigation ---
# -------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Verify Note", "QR Verify", "Database", "About / Deploy"])

# quick theme choices (cosmetic)
theme_choice = st.sidebar.selectbox("Theme", ["Professional (dark header)", "Light"])
if theme_choice == "Light":
    local_css(".header{background:linear-gradient(90deg,#ffffff,#eef2ff); color:#0f172a} .subtitle{color:#475569}")

# -------------------------
# --- PAGES ---------------
# -------------------------
if page == "Home":
    st.markdown("## Welcome")
    st.write(
        """
        This app demonstrates a **simulated** currency verification workflow:
        - Capture/upload an image of a note or coin
        - Choose currency and denomination
        - Run a simulated analysis that shows which security features are visible
        - Get an AI-style explanation text (generated locally)
        - Use a simulated QR verification input (for notes that include QR)
        - Browse a small built-in currency model database for educational reference
        """
    )
    st.info("⚠️ This is a simulation for learning. It does NOT detect real counterfeit currency.")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Money_collage.jpg/640px-Money_collage.jpg", caption="Educational demo", use_column_width=True)
    with col2:
        st.markdown("### Quick demo steps")
        st.markdown("1. Go to **Verify Note** → take/upload photo → select currency/denom → Verify.\n\n"
                    "2. Check the **Security Features Checklist** and the AI-style explanation.\n\n"
                    "3. For QR features, use **QR Verify** page to paste or upload QR text (simulated).")
    with col3:
        st.markdown("### Tips")
        st.markdown("- Use a clear, well-lit photo for better simulated results.\n- This app is for education / UI prototyping only.")

elif page == "Verify Note":
    st.markdown("## Verify Note (Simulated)")
    left, right = st.columns([2, 1])

    with left:
        st.markdown("### 1) Capture / Upload")
        uploaded = st.camera_input("Use your device camera")  # returns UploadedFile or None
        uploaded_fallback = st.file_uploader("Or upload an image", type=["jpg", "jpeg", "png"])
        img_file = uploaded or uploaded_fallback

        st.markdown("### 2) Select currency and denomination")
        currency_map = {v["name"]: k for k, v in CURRENCY_DB.items()}
        currency_display = st.selectbox("Currency", list(currency_map.keys()))
        currency_code = currency_map[currency_display]
        denoms = list(CURRENCY_DB[currency_code]["denominations"].keys())
        denom = st.selectbox("Denomination", denoms)

        st.markdown("### 3) Extra (optional)")
        note_id = st.text_input("Optional note serial / tag (for your records)")
        run_btn = st.button("🔍 Run Verification (Simulated)")

    with right:
        st.markdown("### Upload info")
        if img_file:
            try:
                raw = img_file.getvalue() if hasattr(img_file, "getvalue") else img_file.read()
                st.image(Image.open(io.BytesIO(raw)), caption="Preview", use_column_width=True)
                st.write("File size:", pretty_bytes(len(raw)))
            except Exception as e:
                st.error("Could not preview image.")
        else:
            st.info("No image provided yet — use camera or uploader.")

    if run_btn:
        if not img_file:
            st.error("Please take or upload an image first.")
        else:
            # Read image
            raw = img_file.getvalue() if hasattr(img_file, "getvalue") else img_file.read()
            img = Image.open(io.BytesIO(raw))
            # Simulate analysis
            sim = simulated_analysis(img, currency_code, denom)
            # AI style explanation
            explanation = generate_ai_explanation(sim, CURRENCY_DB[currency_code]["name"], denom)

            st.markdown("## Results")
            colA, colB = st.columns([2, 3])
            with colA:
                if sim["simulated_real"]:
                    st.success("✅ Simulated result: Looks REAL")
                else:
                    st.error("❌ Simulated result: Looks FAKE / Suspicious")

                st.write(f"Simulated confidence (real): {sim['probability_real']*100:.0f}%")
                st.write("Image stats (brightness, contrast, edges):")
                st.json(sim["stats"])

                if note_id:
                    st.write("Record ID:", note_id, "| Scanned at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            with colB:
                st.markdown("### AI-style Explanation (Simulated)")
                st.info(explanation)

            st.markdown("### Security Features Checklist (Simulated)")
            df_rows = []
            for feat in sim["expected_features"]:
                status = "Present" if feat in sim["observed_features"] else "Missing/unclear"
                df_rows.append({"Feature": feat, "Status": status})
            df = pd.DataFrame(df_rows)
            st.table(df)

            if sim["suspicious_reasons"]:
                st.markdown("### Suspicious Findings (Simulated)")
                for s in sim["suspicious_reasons"]:
                    st.write("- " + s)

            st.markdown("---")
            st.write("⚠️ **Reminder:** This is only a simulated educational demo. For real verification contact your bank or currency issuing authority.")

elif page == "QR Verify":
    st.markdown("## QR Verification (Simulated)")
    st.write("Some modern banknotes or supporting documents include QR codes. This page simulates QR verification.")

    col1, col2 = st.columns(2)
    with col1:
        qr_input = st.text_area("Paste QR text (if you have it) or type a sample QR payload here")
        file_qr = st.file_uploader("Or upload a QR image (we will simulate decoding)", type=["png", "jpg", "jpeg"])
        verify_btn = st.button("🔎 Verify QR content")

    with col2:
        st.markdown("### Example QR payloads (paste to left)")
        st.code('{"type":"note","currency":"INR","denom":"200","serial":"ABC123456"}')
        st.code('{"type":"note","currency":"USD","denom":"100","issuer":"FederalReserve"}')
        st.info("This page simulates reading and verifying QR content. We do not perform cryptographic verification here.")

    if verify_btn:
        content = None
        if qr_input.strip():
            content = qr_input.strip()
        elif file_qr:
            # Simulate decode: read file size and pretend to decode
            raw = file_qr.getvalue()
            content = f"(simulated-decoded-from-image size={pretty_bytes(len(raw))})"
        else:
            st.error("Provide QR text or image first.")
        if content:
            st.markdown("### Decoded QR content (SIMULATED)")
            st.code(content)
            # Simple simulated check: if it contains known currency code
            ok = False
            for code in CURRENCY_DB.keys():
                if code in content or CURRENCY_DB[code]["name"].split()[0] in content:
                    ok = True
            if ok:
                st.success("Simulated QR verification: content matches expected currency database.")
            else:
                st.warning("Simulated QR verification: content does not match local database — manual check recommended.")

elif page == "Database":
    st.markdown("## Built-in Currency Model Database (Educational)")
    st.write("This small database includes example denominations and expected security features (for UI/demo only).")
    # Display DB
    rows = []
    for code, meta in CURRENCY_DB.items():
        for denom, feats in meta["denominations"].items():
            rows.append({"Code": code, "Name": meta["name"], "Denomination": denom, "Expected Features": ", ".join(feats)})
    df = pd.DataFrame(rows)
    st.dataframe(df)

    st.markdown("### Export database (JSON-like)")
    st.code(str(CURRENCY_DB))

elif page == "About / Deploy":
    st.markdown("## About this Demo & Deploy Steps")
    st.write("""
    - **What this is:** a *simulated* currency verification prototype for learning and UI prototyping.
    - **Not forensic:** it cannot determine real counterfeit or authenticate notes.
    - **How to deploy on Streamlit Cloud:**
      1. Create GitHub repo and add `app.py`.
      2. Add `requirements.txt` (see below).
      3. Go to https://share.streamlit.io → New app → connect repo → deploy.
    """)
    st.markdown("### Files you should push to GitHub")
    st.code("""
    - app.py   # this file
    - requirements.txt
    - README.md (optional)
    """)

    st.markdown("### Recommended `requirements.txt`")
    st.code("""
    streamlit
    pillow
    pandas
    """)
    st.markdown("### Need help creating GitHub repo structure?")
    if st.button("Generate GitHub-ready zip (simulated)"):
        st.info("I can provide a zipped project structure in a follow-up if you want. (Simulated prompt button)")

# -------------------------
# --- Footer --------------
# -------------------------
st.markdown("---")
st.markdown("© Demo — Educational only. Not a forensic or legal tool.")
