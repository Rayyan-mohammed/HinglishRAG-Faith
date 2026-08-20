"""Week 3 (A2): demo skeleton -- question in, answer out. Claim tags (supported / contradicted /
unverifiable) get added in A4 once Person B wires the verifier into the pipeline."""

import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.pipeline import answer_question
from src.retrieval import load_index

st.set_page_config(page_title="CodeSwitch-Verify", page_icon="🩺")
st.title("CodeSwitch-Verify")
st.caption(
    "Ask about PM-KISAN, Ayushman Bharat, PM Awas Yojana, or Post-Matric Scholarship — in "
    "Hinglish."
)


@st.cache_resource
def get_index():
    return load_index()


index, passages = get_index()

question = st.text_input(
    "Aapka sawaal:", placeholder="e.g. PM-KISAN ke liye eligibility kya hai?"
)

if question:
    with st.spinner("Sochte hain..."):
        result = answer_question(question, index, passages, verify=False)

    st.markdown("### Answer")
    st.write(result["answer"])

    with st.expander("Retrieved sources"):
        for p in result["context_passages"]:
            st.markdown(f"**{p['source']}** (score: {p['score']:.3f})")
            st.caption(p["text"])
