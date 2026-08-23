"""Week 4 (A4): finished demo -- question in, plain answer out, each claim colour-tagged
supported / contradicted / unverifiable against its retrieved evidence, shown alongside the
plain untagged answer for comparison (blueprint Stage 6). Skeleton (question in, answer out)
was built in A3, Week 3."""

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

VERDICT_STYLE = {
    "SUPPORTED": ("🟢", st.success),
    "CONTRADICTED": ("🔴", st.error),
    "UNVERIFIABLE": ("🟡", st.warning),
}


@st.cache_resource
def get_index():
    return load_index()


index, passages = get_index()

question = st.text_input(
    "Aapka sawaal:", placeholder="e.g. PM-KISAN ke liye eligibility kya hai?"
)
verify = st.checkbox(
    "Verify claims against evidence",
    value=True,
    help="Decomposes the answer into atomic claims and checks each one against the retrieved "
    "facts (slower — one extra retrieval + LLM-judge call per claim). Turn off to see the "
    "plain, unverified RAG baseline instead.",
)

if question:
    with st.spinner("Sochte hain..." if not verify else "Sochte hain aur claims check kar rahe hain..."):
        result = answer_question(question, index, passages, verify=verify)

    st.markdown("### Answer")
    st.write(result["answer"])

    if verify:
        st.markdown("### Claims")
        if not result["claims"]:
            st.caption("No individually-checkable claims were decomposed from this answer.")
        for c in result["claims"]:
            icon, renderer = VERDICT_STYLE.get(c["verdict"], ("⚪", st.info))
            renderer(f"{icon} **{c['verdict']}** ({c['confidence']:.2f}) — {c['claim']}")

    with st.expander("Retrieved sources"):
        for p in result["context_passages"]:
            st.markdown(f"**{p['source']}** (score: {p['score']:.3f})")
            st.caption(p["text"])
