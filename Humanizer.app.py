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
    """Executes a cloud model call with an automated backoff retry engine to bypass 429 errors."""
    max_retries = 5
    base_delay = 4  # Starts with a 4-second delay, then doubles exponentially
    
    for attempt in range(max_retries):
        try:
            config_params = {"response_mime_type": mime_type}
            if response_schema:
                config_params["response_schema"] = response_schema
                
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config=types.GenerateContentConfig(**config_params)
            )
            return response.text
        except APIError as e:
            # Catch 429 (Rate Limit) or 503 (Server Overloaded)
            if e.code in [429, 503]:
                sleep_time = base_delay * (2 ** attempt)
                st.warning(f"⚠️ Rate limit boundary hit (429). Pausing workspace for {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
            else:
                raise e  # Raise any other critical API errors instantly
                
    raise Exception("Cloud connections timed out due to sustained quota exhaustion limits.")

# ----------------------------------------------------------------------
# 2. APPLICATION CONFIGURATION & STATE
# ----------------------------------------------------------------------
st.set_page_config(page_title="Forensic Humanizer Workbench", layout="wide")
st.title("🕵️‍♂️ 10k-Word Forensic Style Diagnostician & Humanizer Canvas")
st.write("Streamlined to handle large academic manuscripts by processing chunks dynamically with live validation loops.")

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
    st.caption("Supports up to 10,000+ words. The engine will automatically slice your document cleanly by paragraphs.")
    
    large_text = st.text_area("Paste Manuscript Here:", height=400, placeholder="Paste your massive draft chapters here...")
    
    if st.button("Initialize Deep Style Scan 🔍", type="primary", use_container_width=True):
        if not large_text.strip():
            st.error("Please provide text to initialize the processing workspace layers.")
        else:
            with st.spinner("Slicing text blocks and preparing tracking matrix variables..."):
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
    
    total_p = len(st.session_state.document_chunks)
    passed_p = sum(1 for c in st.session_state.document_chunks if c["status"] == "🟢 Humanized & Verified")
    flagged_p = total_p - passed_p
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Paragraph Blocks", total_p)
    col_m2.metric("🟢 Passed (Human Tone)", passed_p)
    col_m3.metric("🔴 Flagged (AI Signature)", flagged_p)
    
    st.divider()
    
    options_list = [f"Paragraph {i+1} [{st.session_state.document_chunks[i]['status']}]" for i in range(total_p)]
    selected_index = st.selectbox("Select Paragraph to Scan / Edit:", range(total_p), format_func=lambda x: options_list[x])
    
    active_block = st.session_state.document_chunks[selected_index]
    
    if active_block["status"] == "🟢 Humanized & Verified":
        st.success("🟢 Style Status: Verified Human Cadence. Excellent structural variance.")
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
                with st.spinner("Analyzing paragraph cadence profiles..."):
                    audit_prompt = f"""
                    You are an elite academic developmental editor. Analyze this specific paragraph sentence-by-sentence.
                    1. Highlight sentences that sound robotic due to monotone rhythm, predictable word choice, or cliché academic connectors.
                    2. State exactly WHY it feels like AI (e.g., 'Low perplexity', 'Starts with a predictable transition word').
                    3. Provide an organic, elegant 'Human Blueprint Rewrite' that alters sentence lengths and restores authentic scholarly voice.

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
                        # Routed via our smart retry engine function
                        res_raw = call_gemini_with_retry(audit_prompt, response_schema=schema_audit)
                        audit_data = json.loads(res_raw)
                        
                        if audit_data["is_robotic"]:
                            st.session_state.document_chunks[selected_index]["status"] = "🔴 Flagged (AI Signature Detected)"
                        else:
                            st.session_state.document_chunks[selected_index]["status"] = "🟢 Humanized & Verified"
                            
                        st.session_state.document_chunks[selected_index]["feedback"] = (
                            f"**Overall Assessment:** {audit_data['critique_notes']}\n\n"
                            f"**Sentence-Level Breakdown:**\n{audit_data['sentence_by_sentence_breakdown']}"
                        )
                        st.session_state.document_chunks[selected_index]["blueprint"] = audit_data["suggested_human_blueprint"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Linguistic processing failure: {e}")
                        
        with col_buttons[1]:
            if active_block["blueprint"]:
                if st.button("Apply Suggested Blueprint Instantly 💡", use_container_width=True):
                    st.session_state.document_chunks[selected_index]["current"] = active_block["blueprint"]
                    st.session_state.document_chunks[selected_index]["status"] = "🟢 Humanized & Verified"
                    st.toast("Blueprint applied seamlessly!", icon="✅")
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
    st.success("All sections processed into a consolidated view framework.")
    
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