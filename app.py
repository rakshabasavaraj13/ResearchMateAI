
import streamlit as st
import sys
import os

st.set_page_config(
    page_title="ResearchMate AI",
    page_icon="📚",
    layout="wide"
)

# ============================================================
# Imports
# ============================================================

sys.path.insert(
    0,
    os.path.dirname(os.path.abspath(__file__))
)

from research_agent import run_full_research_agent
from report_export import create_pdf, create_docx


# ============================================================
# Header
# ============================================================

st.title("📚 ResearchMate AI")

st.markdown(
    """
    ### Autonomous Academic Research Agent

    Enter **any research topic** and ResearchMate AI will:

    🔬 Plan the research  
    📚 Search academic literature  
    🧠 Analyze research papers  
    📊 Compare existing studies  
    🔎 Identify research gaps  
    📝 Generate a literature survey  
    📄 Generate an academic research report  
    ⬇️ Download the report as PDF or DOCX
    """
)

st.divider()


# ============================================================
# Input
# ============================================================

topic = st.text_input(
    "🔎 Enter your research topic",
    placeholder="Example: Quantum Computing and Cryptography"
)

max_papers = st.selectbox(
    "📚 Number of papers to analyze",
    [3, 5, 8, 10],
    index=1
)

generate = st.button(
    "🚀 Generate Research Report",
    type="primary",
    use_container_width=True
)


# ============================================================
# Research
# ============================================================

if generate:

    if not topic.strip():

        st.warning(
            "⚠️ Please enter a research topic."
        )

    else:

        with st.status(
            "🔬 ResearchMate AI is working...",
            expanded=True
        ) as status:

            try:

                st.write(
                    "🧠 Creating research plan..."
                )

                result = run_full_research_agent(
                    topic.strip(),
                    max_papers=max_papers
                )

                status.update(
                    label="✅ Research completed!",
                    state="complete",
                    expanded=False
                )

                st.session_state[
                    "research_result"
                ] = result

            except Exception as e:

                status.update(
                    label="❌ Research failed",
                    state="error"
                )

                st.error(
                    f"Research engine error: {e}"
                )


# ============================================================
# Report
# ============================================================

result = st.session_state.get(
    "research_result"
)


if result:

    report = result["academic_report"]

    st.divider()

    st.header("📄 Academic Research Report")

    st.markdown(report)

    st.divider()

    st.subheader("📥 Download Your Research")

    # Generate files
    pdf_data = create_pdf(report)
    docx_data = create_docx(report)

    col1, col2 = st.columns(2)

    with col1:

        st.download_button(
            "📄 Download PDF",
            data=pdf_data,
            file_name=(
                topic.strip().replace(" ", "_")
                + "_Research_Report.pdf"
            ),
            mime="application/pdf",
            use_container_width=True
        )

    with col2:

        st.download_button(
            "📝 Download DOCX",
            data=docx_data,
            file_name=(
                topic.strip().replace(" ", "_")
                + "_Research_Report.docx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            use_container_width=True
        )

    st.success(
        "🎉 Your academic research report is ready!"
    )
