import hashlib
import re
import secrets
from datetime import datetime
from io import BytesIO

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

st.set_page_config(
    page_title="BAN 517 Inventory Agent Report Generator",
    page_icon="📦",
    layout="wide",
)

COURSE = "BAN 517: Supply Chain Analytics"
PROJECT = "Inventory Analytics Agent Project"
APP_TITLE = "Inventory Agent Project Report Generator"

TESTS = [
    (
        "Test 1 - Portfolio Summary",
        "How many SKUs are in each final inventory class? Show the total sales for each class.",
    ),
    (
        "Test 2 - Class A Inventory",
        "Show me all Class A inventory items. Include SKU, Sales, POS Hits, Sales Class, Hits Class, combined score, and final inventory class.",
    ),
    (
        "Test 3 - Top Class A Items",
        "Show me the top 5 Class A inventory items ranked by Sales.",
    ),
    (
        "Test 4 - Classification Process",
        "For SKU 1170, show how its final inventory classification was determined. Show the Sales classification, POS Hits classification, combined score, and final class.",
    ),
    (
        "Test 5 - Class A Inventory Policy",
        "What inventory-management policy would you recommend for Class A inventory?",
    ),
    (
        "Test 6 - Apply Policy to the Portfolio",
        "Show the top 5 Class A items by Sales and include the recommended inventory-management policy for these items.",
    ),
    (
        "Test 7 - EOQ",
        "Find EOQ. Demand is 1,000 units per month, ordering cost is $25 per order, and holding cost is $0.50 per unit per year.",
    ),
    (
        "Test 8 - Safety Stock and Reorder Point",
        "A product has average demand of 40 units per day with a standard deviation of 8 units per day. Average lead time is 3 weeks with a standard deviation of 0.5 weeks. Determine the safety stock and reorder point for a 95% service level.",
    ),
    (
        "Test 9 - Quantity Discount",
        "Annual demand is 5,000 units. Ordering cost is $60 per order and annual holding cost is 20% of unit cost. The supplier charges $12 per unit for orders below 500 units, $11.50 for 500-999 units, and $11 for orders of 1,000 units or more. Find the best order quantity and annual cost.",
    ),
]


def esc(value):
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def report_id(student_name, app_url, generated_at):
    salt = secrets.token_hex(4)
    raw = f"{student_name}|{app_url}|{generated_at}|{salt}".encode("utf-8")
    return "INV-" + hashlib.sha256(raw).hexdigest()[:12].upper()


def response_to_paragraphs(text, style):
    """Preserve readable paragraph breaks without treating pasted text as markup."""
    cleaned = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    blocks = re.split(r"\n\s*\n", cleaned)
    flow = []
    for block in blocks:
        block = esc(block).replace("\n", "<br/>")
        if block:
            flow.append(Paragraph(block, style))
            flow.append(Spacer(1, 5))
    return flow


def build_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.62 * inch,
        rightMargin=0.62 * inch,
        topMargin=0.60 * inch,
        bottomMargin=0.60 * inch,
        title=f"{PROJECT} Verification Report",
        author=COURSE,
    )

    styles = getSampleStyleSheet()
    navy = colors.HexColor("#003B5C")
    teal = colors.HexColor("#006C67")
    light_teal = colors.HexColor("#F4FBFB")
    light_blue = colors.HexColor("#EEF7FF")
    light_gray = colors.HexColor("#F5F7F9")
    border = colors.HexColor("#D7E0E8")
    body = colors.HexColor("#0B2239")

    styles.add(ParagraphStyle(
        name="RptTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=navy, alignment=TA_CENTER, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="RptSub", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10, leading=13, textColor=teal, alignment=TA_CENTER, spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name="RptH", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=navy, spaceBefore=9, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="RptBody", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.3, leading=13, textColor=body, spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name="RptPrompt", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=9.2, leading=13, textColor=navy, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="RptSmall", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=7.8, leading=10, textColor=colors.HexColor("#5D6B78")
    ))

    story = [
        Paragraph(PROJECT, styles["RptTitle"]),
        Paragraph(f"{COURSE} | Project Verification Report", styles["RptSub"]),
    ]

    meta = [
        ["Student", esc(data["student_name"])],
        ["Deployed Inventory Agent", esc(data["agent_url"])],
        ["Generated", esc(data["generated_at"])],
        ["Report ID", esc(data["report_id"])],
    ]
    mt = Table(meta, colWidths=[1.65 * inch, 5.15 * inch])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), light_blue),
        ("TEXTCOLOR", (0,0), (0,-1), navy),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.3),
        ("BOX", (0,0), (-1,-1), 0.6, border),
        ("INNERGRID", (0,0), (-1,-1), 0.3, border),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story += [mt, Spacer(1, 10)]

    note = Table([[
        Paragraph(
            "<b>Submission record:</b> The responses below were entered by the student "
            "from the final version of the deployed Inventory Analytics Agent identified above.",
            styles["RptBody"]
        )
    ]], colWidths=[6.8 * inch])
    note.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), light_teal),
        ("BOX", (0,0), (-1,-1), 0.6, colors.HexColor("#B9DEDA")),
        ("LEFTPADDING", (0,0), (-1,-1), 9),
        ("RIGHTPADDING", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story += [note, Spacer(1, 8)]

    for idx, ((title, prompt), answer) in enumerate(zip(TESTS, data["answers"])):
        if idx == 6:
            story.append(PageBreak())
            story.append(Paragraph("Inventory Decision Agent Validation", styles["RptH"]))

        story.append(Paragraph(title, styles["RptH"]))

        prompt_box = Table([[
            Paragraph("<b>Prompt</b><br/>" + esc(prompt), styles["RptBody"])
        ]], colWidths=[6.8 * inch])
        prompt_box.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), light_blue),
            ("BOX", (0,0), (-1,-1), 0.5, border),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ]))
        story += [prompt_box, Spacer(1, 5)]
        story.append(Paragraph("<b>Final Agent Response</b>", styles["RptPrompt"]))

        response_flow = response_to_paragraphs(answer, styles["RptBody"])
        response_box = Table([[
            response_flow
        ]], colWidths=[6.8 * inch])
        response_box.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.white),
            ("BOX", (0,0), (-1,-1), 0.5, border),
            ("LEFTPADDING", (0,0), (-1,-1), 9),
            ("RIGHTPADDING", (0,0), (-1,-1), 9),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        story += [response_box, Spacer(1, 7)]

    story.append(PageBreak())
    story.append(Paragraph("Student Certification", styles["RptH"]))

    certs = [
        "I confirm that all responses entered in this report were generated by the final version of the Streamlit Inventory Analytics Agent that I developed and deployed for this project.",
        "I confirm that I reviewed the classifications, calculations, units, assumptions, and recommendations using the inventory analytics methods covered in this course and corrected my application where necessary before generating this report.",
    ]

    ct = Table(
        [["Confirmed", Paragraph(esc(certs[0]), styles["RptBody"])],
         ["Confirmed", Paragraph(esc(certs[1]), styles["RptBody"])]],
        colWidths=[1.0 * inch, 5.8 * inch],
    )
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), light_teal),
        ("TEXTCOLOR", (0,0), (0,-1), teal),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("BOX", (0,0), (-1,-1), 0.6, border),
        ("INNERGRID", (0,0), (-1,-1), 0.3, border),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story += [ct, Spacer(1, 12)]
    story.append(Paragraph(f"<b>Certified by:</b> {esc(data['student_name'])}", styles["RptBody"]))
    story.append(Paragraph(
        "This report records the final responses submitted by the student. "
        "The report generator does not independently determine whether the analytical answers are correct.",
        styles["RptSmall"]
    ))

    def footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#5D6B78"))
        canvas.drawString(0.62 * inch, 0.32 * inch, COURSE)
        canvas.drawRightString(
            letter[0] - 0.62 * inch, 0.32 * inch,
            f"{data['report_id']} | Page {doc_obj.page}"
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ---------- UI ----------

st.markdown("""
<style>
.block-container {max-width: 1050px; padding-top: 2rem; padding-bottom: 4rem;}
div[data-testid="stTextArea"] textarea {font-size: 0.95rem;}
.prompt-box {
    background: #eef7ff;
    border-left: 5px solid #3b82b8;
    border-radius: 8px;
    padding: 12px 15px;
    margin: 8px 0 10px 0;
}
.section-note {
    background: #f4fbfb;
    border-left: 5px solid #008c95;
    border-radius: 8px;
    padding: 12px 15px;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

st.title(APP_TITLE)
st.caption(COURSE)

st.markdown(
    """
<div class="section-note">
<b>Complete this report only after you have finished testing and correcting your Inventory Analytics Agent.</b>
For each test, run the prompt exactly as shown in your final deployed agent, review the result, and paste the final agent response into the corresponding answer box.
</div>
""",
    unsafe_allow_html=True,
)

c1, c2 = st.columns([1, 2])
with c1:
    student_name = st.text_input(
        "Student Name",
        placeholder="Enter your full name",
        key="student_name",
    )
with c2:
    agent_url = st.text_input(
        "Deployed Inventory Agent URL",
        placeholder="https://your-inventory-agent.streamlit.app",
        key="agent_url",
    )

st.divider()
st.header("Part 1 - Multicriteria Inventory Classification and Policy")

answers = []

for i, (title, prompt) in enumerate(TESTS[:6], start=1):
    st.subheader(title)
    st.markdown(
        f'<div class="prompt-box"><b>Prompt</b><br>{esc(prompt)}</div>',
        unsafe_allow_html=True,
    )
    answers.append(
        st.text_area(
            "Paste the final response from your Inventory Analytics Agent",
            height=180 if i != 2 else 260,
            key=f"answer_{i}",
            placeholder="Paste the complete final response here.",
        )
    )

st.divider()
st.header("Part 2 - Inventory Decision Agent Validation")
st.caption(
    "Run these prompts in the final version of your agent. Review the calculations, units, assumptions, "
    "and recommendations before entering the response here."
)

for i, (title, prompt) in enumerate(TESTS[6:], start=7):
    st.subheader(title)
    st.markdown(
        f'<div class="prompt-box"><b>Prompt</b><br>{esc(prompt)}</div>',
        unsafe_allow_html=True,
    )
    answers.append(
        st.text_area(
            "Paste the final response from your Inventory Analytics Agent",
            height=230,
            key=f"answer_{i}",
            placeholder="Paste the complete final response here.",
        )
    )

st.divider()
st.header("Student Certification")

cert1 = st.checkbox(
    "I confirm that all responses entered in this report were generated by the final version "
    "of the Streamlit Inventory Analytics Agent that I developed and deployed for this project."
)
cert2 = st.checkbox(
    "I confirm that I reviewed the classifications, calculations, units, assumptions, and "
    "recommendations using the inventory analytics methods covered in this course and corrected "
    "my application where necessary before generating this report."
)

errors = []
if not student_name.strip():
    errors.append("Enter your name.")
if not agent_url.strip():
    errors.append("Enter your deployed Inventory Agent URL.")
elif not re.match(r"^https?://", agent_url.strip(), flags=re.I):
    errors.append("Enter the complete deployed app URL beginning with https://.")
for i, ans in enumerate(answers, start=1):
    if not ans.strip():
        errors.append(f"Complete Test {i}.")
if not cert1 or not cert2:
    errors.append("Complete both certification statements.")

if errors:
    with st.expander("Report requirements not yet complete"):
        for e in errors:
            st.write(f"- {e}")

if st.button(
    "Generate Project Verification Report",
    type="primary",
    disabled=bool(errors),
):
    generated_at = datetime.now().astimezone().strftime("%B %d, %Y at %I:%M %p %Z")
    rid = report_id(student_name.strip(), agent_url.strip(), generated_at)

    data = {
        "student_name": student_name.strip(),
        "agent_url": agent_url.strip(),
        "generated_at": generated_at,
        "report_id": rid,
        "answers": [a.strip() for a in answers],
    }

    try:
        pdf_bytes = build_pdf(data)
        st.session_state["pdf_bytes"] = pdf_bytes
        st.session_state["rid"] = rid
        st.session_state["safe_name"] = re.sub(
            r"[^A-Za-z0-9_-]+", "_", student_name.strip()
        ).strip("_")
        st.success(f"Report generated successfully. Report ID: {rid}")
    except Exception as exc:
        st.error("The PDF could not be generated.")
        st.exception(exc)

if "pdf_bytes" in st.session_state:
    st.download_button(
        "Download Project Verification Report (PDF)",
        data=st.session_state["pdf_bytes"],
        file_name=f"BAN517_Inventory_Agent_Report_{st.session_state['safe_name']}.pdf",
        mime="application/pdf",
    )
