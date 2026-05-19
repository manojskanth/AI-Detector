import streamlit as st
import json
import re
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

# ----------------------------------------------------------------------
# 1. API INITIALIZATION & RATE-LIMIT RESILIENT WRAPPER
# ----------------------------------------------------------------------
client = genai.Client(api_key="AIzaSyBGnTLwQ-MBPBWF0arK2vdr-47lf3L4F70")

def call_gemini_with_retry(prompt, response_schema=None, mime_type="application/json"):
    """
    Executes a cloud model call using the high-volume gemini-2.5-flash engine.
    Includes a baseline throttle and robust exponential backoff retry states.
    """
    max_retries = 5
    base_delay = 5  # Initial wait window in seconds
    
    # Pre-flight pacing safety gap to stabilize Tokens-Per-Minute consumption
    time.sleep(1.5) 
    
    for attempt in range(max_retries):
        try:
            config_params = {"response_mime_type": mime_type}
            if response_schema:
                config_params["response_schema"] = response_schema
                
            response = client.models.generate_content(
                model='gemini-2.5-flash', # Optimized for rapid, high-throughput pay-as-you-go processing
                contents=prompt,
                config=types.GenerateContentConfig(**config_params)
            )
            return response.text
        except APIError as e:
            if e.code in [429, 503]:
                sleep_time = base_delay * (2 ** attempt) 
                st.warning(f"⚠️ Cloud Rate-Limit Pacing Guard Triggered. Pausing app execution flow for {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                raise e
                
    raise Exception("Cloud connection timed out due to sustained quota congestion. Please try again in a moment.")

# ----------------------------------------------------------------------
# 2. APPLICATION CONFIGURATION & STATE
# ----------------------------------------------------------------------
st.set_page_config(page_title="Forensic Humanizer Workbench", layout="wide")
st.title("🕵️‍♂️ 10k-Word Forensic Style Diagnostician & Humanizer Canvas")
st.write("A high-throughput text validation workspace engineered for large academic manuscripts and faculty collaboration.")

if "document_chunks" not in st.session_state:
    st.session_state.document_chunks = []
if "step" not in st.session_state:
    st.session_state.step = 1

st.divider()

# ----------------------------------------------------------------------
# STEP 1: INITIAL PASTE & CHUNK EXTRACTION LAYERS
# ----------------------------------------------------------------------
if st.session_state.step == 1:
    st.header("Step 1: Paste Your Large Manuscript")
    st.caption("Supports massive texts (up to 10,000+ words). The script splits your content by paragraphs into safe operational memory segments.")
    
    large_text = st.text_area("Paste Manuscript Here:", height=400, placeholder="Paste your chapters or research draft segments here...")
    
    if st.button("Initialize Deep Style Scan 🔍", type="primary", use_container_width=True):
        if not large_text.strip():
            st.error("Please provide text to initialize the processing workspace layers.")
        else:
            with st.spinner("Slicing text structures and parsing baseline layout matrix..."):
                # Clean split handling paragraph double breaks safely
                raw_paragraphs = [p.strip() for p in large_text.split("\n\n") if p.strip()]
                
                st.session_state.document_chunks = []
                for p in raw_paragraphs:
                    st.session_state.document_chunks.append({
                        "original": p,
                        "current": p,
                        "status": "🔴 Flagged (Pending Review)",
                        "feedback": "Paragraph queued up for deep sentence-level style assessment.",
                        "blueprint": ""
                    })
                st.session_state.step = 2
                st.rerun()

# ----------------------------------------------------------------------
# STEP 2: LIVE INTERACTIVE HIGHLIGHT & WORKBENCH EDITOR
# ----------------------------------------------------------------------
elif st.session_state.step == 2:
    st.header("Step 2: Interactive Prose Validation Desk")
    st.write("Navigate through individual paragraph units below. Green states represent verified human syntax profiles.")
    
    total_p = len(st.session_state.document_chunks)
    passed_p = sum(1 for c in st.session_state.document_chunks if c["status"] == "🟢 Humanized & Verified")
    flagged_p = total_p - passed_p
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Paragraph Blocks", total_p)
    col_m2.metric("🟢 Passed (Human Tone)", passed_p)
    col_m3.metric("🔴 Flagged (AI Signature)", flagged_p)
    
    st.divider()
    
    options_list = [f"Paragraph {i+1} [{st.session_state.document_chunks[i]['status']}]" for i in range(total_p)]
    selected_index = st.selectbox("Select Paragraph Block to Scan / Refine:", range(total_p), format_func=lambda x: options_list[x])
    
    active_block = st.session_state.document_chunks[selected_index]
    
    if active_block["status"] == "🟢 Humanized & Verified":
        st.success("🟢 Style Status: Verified Human Cadence. Structural variance profiles acceptable.")
    else:
        st.error(f"🔴 Style Status: {active_block['status']}")
        
    col_edit, col_diagnostics = st.columns([6, 5])
    
    with col_edit:
        st.subheader("📝 Live Paragraph Editor")
        user_edit_text = st.text_area(
            "Modify text content here directly:",
            value=active_block["current"],
            height=300,
            key=f"text_area_{selected_index}"
        )
        st.session_state.document_chunks[selected_index]["current"] = user_edit_text
        
        col_buttons = st.columns([1, 1])
        with col_buttons[0]:
            if st.button("Execute Sentence-Level Style Audit ⚡", type="primary", use_container_width=True):
                with st.spinner("Analyzing paragraph syntax and cadence profiles..."):
                    audit_prompt = f"""
                    You are an elite academic editor profiling prose for artificial linguistic signatures.
                    Analyze this paragraph sentence-by-sentence:
                    1. Highlight sentences that sound robotic due to monotone lengths, formulaic transitions, or low perplexity.
                    2. Detail exactly WHY it sounds artificial (e.g., cliché connector word, predictable patterns).
                    3. Provide an organic, elegant 'Human Blueprint Rewrite' that introduces varied sentence structures, a professional tone, and authentic human flow.

                    PARAGRAPH TO AUDIT:
                    {user_edit_text}
                    """
                    
                    schema_audit = types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "is_robotic": types.Schema(type=types.Type.BOOLEAN),
                            "critique_notes": types.Schema(type=types.Type.STRING),
                            "sentence_by_sentence_breakdown": types.Schema(type=types.Type.STRING),
                            "suggested_human_blueprint": types.Schema(type=types.Type.STRING)
                        },
                        required=["is_robotic", "critique_notes", "sentence_by_sentence_breakdown", "suggested_human_blueprint"]
                    )
                    
                    try:
                        res_raw = call_gemini_with_retry(audit_prompt, response_schema=schema_audit)
                        audit_data = json.loads(res_raw)
                        
                        if audit_data["is_robotic"]:
                            st.session_state.document_chunks[selected_index]["status"] = "🔴 Flagged (AI Signature Detected)"
                        else:
                            st.session_state.document_chunks[selected_index]["status"] = "🟢 Humanized & Verified"
                            
                        st.session_state.document_chunks[selected_index]["feedback"] = (
                            f"**Overall Assessment:** {audit_data['critique_notes']}\n\n"
                            f"**Sentence-by-Sentence Audit:**\n{audit_data['sentence_by_sentence_breakdown']}"
                        )
                        st.session_state.document_chunks[selected_index]["blueprint"] = audit_data["suggested_human_blueprint"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Linguistic diagnostic pipeline broken: {e}")
                        
        with col_buttons[1]:
            if active_block["blueprint"]:
                if st.button("Apply Suggested Blueprint Instantly 💡", use_container_width=True):
                    st.session_state.document_chunks[selected_index]["current"] = active_block["blueprint"]
                    st.session_state.document_chunks[selected_index]["status"] = "🟢 Humanized & Verified"
                    st.toast("Polished blueprint injected successfully!", icon="✅")
                    st.rerun()

    with col_diagnostics:
        st.subheader("🔍 Forensic Metrics & Blueprints")
        with st.container(border=True):
            st.markdown("### 📊 Structural Vulnerability Analysis")
            st.markdown(active_block["feedback"])
            
            if active_block["blueprint"]:
                st.divider()
                st.markdown("### 💡 Recommended Human Blueprint Rewrite")
                st.info(active_block["blueprint"])

    st.divider()
    st.subheader("🚀 Reassemble Clean Final Manuscript")
    if st.button("Compile & Render Full Humanized Text ➡️", use_container_width=True):
        st.session_state.step = 3
        st.rerun()

# ----------------------------------------------------------------------
# STEP 3: REASSEMBLED MANUSCRIPT EXPORT PREVIEW
# ----------------------------------------------------------------------
elif st.session_state.step == 3:
    st.header("Step 3: Export Your Polished Manuscript")
    st.success("All text components consolidated successfully.")
    
    compiled_manuscript = "\n\n".join([c["current"] for c in st.session_state.document_chunks])
    st.text_area("Final Clean Compiled Document Output:", value=compiled_manuscript, height=450)
    
    col_foot = st.columns([1, 3])
    with col_foot[0]:
        if st.button("⏮️ Return to Workbench"):
            st.session_state.step = 2
            st.rerun()
    with col_foot[1]:
        if st.button("Process an Entirely New Document Draft File 📑", use_container_width=True):
            st.session_state.step = 1
            st.session_state.document_chunks = []
            st.rerun()