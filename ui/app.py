"""
ui/app.py — MomFlow AI Streamlit Interface.

Features:
  • Text input mode (always available — no mic needed for demo/eval)
  • Audio file upload mode
  • Live microphone recording (requires st-audiorec package)
  • Real-time pipeline display with per-stage status
  • Bilingual output display (EN + HI side by side)

Run:
    streamlit run ui/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

# Add parent to path so app imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.main import run_pipeline

# ── Page config ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MomFlow AI — Mumzworld",
    page_icon="🛍️",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;700&family=DM+Sans:wght@400;600&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #C8375B;
        margin-bottom: 0;
    }
    .subtitle { color: #888; margin-top: 0; font-size: 1rem; }

    .response-card {
        background: #f9f9f9;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border-left: 4px solid #C8375B;
        margin-bottom: 1rem;
    }
    .response-card-hi {
        direction: ltr;
        text-align: left;
        font-family: 'Noto Sans Devanagari', sans-serif;
        font-size: 1.05rem;
        border-left: none;
        border-right: 4px solid #E8A020;
    }
    .item-badge {
        display: inline-block;
        background: #FFF0F4;
        color: #C8375B;
        border: 1px solid #F5C0CE;
        border-radius: 20px;
        padding: 3px 12px;
        margin: 4px;
        font-size: 0.85rem;
    }
    .confidence-bar { height: 8px; border-radius: 4px; background: #eee; }
    .refusal-box {
        background: #FFF8E1;
        border: 1px solid #FFD54F;
        border-radius: 10px;
        padding: 1rem;
        color: #7B5800;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────

st.markdown('<p class="main-title">🛍️ MomFlow AI</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Voice & text shopping assistant for Mumzworld — English & Hindi</p>',
    unsafe_allow_html=True,
)
st.divider()

# ── Input Section ──────────────────────────────────────────────────────────

col_in, col_out = st.columns([1, 1], gap="large")

with col_in:
    st.subheader("📥 Input")

    input_mode = st.radio(
        "Input mode",
        ["✍️ Type text", "🎙️ Upload audio"],
        horizontal=True,
        label_visibility="collapsed",
    )

    text_input = ""
    audio_path = None
    language_hint = "en"

    if input_mode == "✍️ Type text":
        language_hint = st.selectbox(
            "Language", ["English (en)", "Hindi (hi)"],
            index=0
        )
        language_hint = "hi" if "hi" in language_hint else "en"

        text_input = st.text_area(
            "What does mom need?",
            placeholder=(
                "e.g. I need Pampers size 4 and baby lotion next week\n"
                "या: मुझे डायपर साइज 3 और बेबी लोशन चाहिए"
            ),
            height=130,
        )

    elif input_mode == "🎙️ Upload audio":
        uploaded = st.file_uploader(
            "Upload a voice memo (.wav, .mp3, .m4a)",
            type=["wav", "mp3", "m4a", "ogg", "webm"],
        )
        if uploaded:
            tmp_path = Path("/tmp") / uploaded.name
            tmp_path.write_bytes(uploaded.read())
            audio_path = str(tmp_path)
            st.audio(str(tmp_path))

    run_btn = st.button("🚀 Process", use_container_width=True, type="primary")

# ── Pipeline Execution ─────────────────────────────────────────────────────

with col_out:
    st.subheader("📤 Output")

    if run_btn:
        if not text_input.strip() and not audio_path:
            st.warning("Please enter text or upload an audio file.")
        else:
            with st.spinner("Running MomFlow AI pipeline…"):
                result = run_pipeline(
                    audio_path=audio_path,
                    text=text_input if text_input.strip() else None,
                    language_hint=language_hint,
                )

            if "error" in result:
                st.error(f"Pipeline error at stage **{result.get('stage', '?')}**: {result['error']}")

            elif result.get("refusal"):
                st.markdown(
                    f'<div class="refusal-box">⚠️ <strong>MomFlow couldn\'t process this request</strong><br>'
                    f'{result["refusal"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("**हिन्दी:**")
                st.markdown(
                    f'<div class="response-card response-card-hi">{result.get("response_hi", "")}</div>',
                    unsafe_allow_html=True,
                )

            else:
                # ── Confidence ──────────────────────────────────────────
                conf = result.get("confidence", 0)
                conf_color = "#2ECC71" if conf >= 0.75 else ("#F39C12" if conf >= 0.5 else "#E74C3C")
                st.markdown(
                    f"**Confidence:** {conf:.0%} &nbsp;"
                    f'<span style="color:{conf_color}">●</span>',
                    unsafe_allow_html=True,
                )

                # ── Shopping list ───────────────────────────────────────
                shopping = result.get("shopping_list", [])
                if shopping:
                    st.markdown("**🛒 Shopping List:**")
                    badges = ""
                    for item in shopping:
                        label = item["item"]
                        if item.get("details"):
                            label += f" ({item['details']})"
                        if item.get("quantity"):
                            label = f"{item['quantity']}× {label}"
                        badges += f'<span class="item-badge">{label}</span>'
                    st.markdown(badges, unsafe_allow_html=True)

                # ── Schedule ────────────────────────────────────────────
                schedule = result.get("schedule", [])
                if schedule:
                    st.markdown("**📅 Schedule:**")
                    for entry in schedule:
                        st.markdown(f"- {entry['task']} — *{entry['date']}*")

                # ── Bilingual responses ─────────────────────────────────
                st.markdown("---")
                r_col1, r_col2 = st.columns(2)

                with r_col1:
                    st.markdown("**🇬🇧 English**")
                    st.markdown(
                        f'<div class="response-card">{result.get("response_en", "")}</div>',
                        unsafe_allow_html=True,
                    )

                with r_col2:
                    st.markdown("**�� हिन्दी**")
                    st.markdown(
                        f'<div class="response-card response-card-hi">{result.get("response_hi", "")}</div>',
                        unsafe_allow_html=True,
                    )

                # ── Raw JSON expander ───────────────────────────────────
                with st.expander("🔍 Raw JSON output"):
                    st.json(result)

    else:
        st.info("Enter your input on the left and click **Process** to run the pipeline.")

# ── Footer ─────────────────────────────────────────────────────────────────
st.divider()
st.caption("MomFlow AI — Built for Mumzworld AI Engineering Internship Assessment")