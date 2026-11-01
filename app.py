import hashlib, re, secrets
from datetime import datetime
from io import BytesIO

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

st.set_page_config(page_title="BAN 517 Inventory Agent Report Generator", page_icon="📦", layout="wide")

COURSE = "BAN 517: Supply Chain Analytics"
PROJECT = "Inventory Analytics Agent Project"

POLICY_QUESTIONS = [
    (
        "Question 4 - Class A Inventory Policy",
        "What inventory-management policy would you recommend for Class A inventory?"
    ),
    (
        "Question 5 - Apply Policy to the Portfolio",
        "Using the top 5 Class A items you identified, explain how you would manage these items and why."
    ),
]

AUDIT_PROMPTS = [
    (
        "Test 6 - EOQ",
        "Find EOQ. Demand is 1,000 units per month, ordering cost is $25 per order, and holding cost is $0.50 per unit per year."
    ),
    (
        "Test 7 - Safety Stock and Reorder Point",
        "A product has average demand of 40 units per day with a standard deviation of 8 units per day. Average lead time is 3 weeks with a standard deviation of 0.5 weeks. Determine the safety stock and reorder point for a 95% service level."
    ),
    (
        "Test 8 - Quantity Discount",
        "Annual demand is 5,000 units. Ordering cost is $60 per order and annual holding cost is 20% of unit cost. The supplier charges $12 per unit for orders below 500 units, $11.50 for 500-999 units, and $11 for orders of 1,000 units or more. Find the best order quantity and annual cost."
    ),
]

def esc(x):
    return str(x or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def make_id(name, url, ts):
    raw = f"{name}|{url}|{ts}|{secrets.token_hex(4)}".encode()
    return "INV-" + hashlib.sha256(raw).hexdigest()[:12].upper()

def text_flow(text, style):
    out = []
    for block in re.split(r"\n\s*\n", str(text or "").strip()):
        if block.strip():
            out += [Paragraph(esc(block).replace("\n","<br/>"), style), Spacer(1,4)]
    return out

def build_pdf(d):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=.62*inch, rightMargin=.62*inch,
        topMargin=.58*inch, bottomMargin=.58*inch
    )
    s = getSampleStyleSheet()
    navy=colors.HexColor("#003B5C"); teal=colors.HexColor("#006C67")
    lt=colors.HexColor("#F4FBFB"); lb=colors.HexColor("#EEF7FF")
    bd=colors.HexColor("#D7E0E8"); body=colors.HexColor("#0B2239")
    s.add(ParagraphStyle(name="T",parent=s["Title"],fontName="Helvetica-Bold",fontSize=18,leading=22,textColor=navy,alignment=TA_CENTER))
    s.add(ParagraphStyle(name="H",parent=s["Heading2"],fontName="Helvetica-Bold",fontSize=12,leading=15,textColor=navy,spaceBefore=9,spaceAfter=6))
    s.add(ParagraphStyle(name="B",parent=s["BodyText"],fontSize=9.2,leading=13,textColor=body,spaceAfter=4))
    s.add(ParagraphStyle(name="S",parent=s["BodyText"],fontSize=7.8,leading=10,textColor=colors.HexColor("#5D6B78")))

    story = [
        Paragraph(PROJECT, s["T"]),
        Paragraph(COURSE + " | Project Verification Report", s["B"]),
        Spacer(1,7)
    ]

    meta = [
        ["Student", esc(d["name"])],
        ["Deployed Inventory Agent", esc(d["url"])],
        ["Generated", d["ts"]],
        ["Report ID", d["rid"]],
    ]
    t=Table(meta,colWidths=[1.65*inch,5.15*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),lb),("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("BOX",(0,0),(-1,-1),.5,bd),("INNERGRID",(0,0),(-1,-1),.3,bd),
        ("FONTSIZE",(0,0),(-1,-1),8.3),("PADDING",(0,0),(-1,-1),6)
    ]))
    story += [t, Spacer(1,8)]

    story += [Paragraph("Part 1 - Multicriteria Inventory Classification Results", s["H"])]
    story += [Paragraph(
        "The student transcribed these results from the final classification output produced by the deployed Streamlit application.",
        s["B"]
    )]

    story += [Paragraph("Final Inventory Classification Prompt", s["H"])]
    story += [Paragraph(
        "Final prompt used in Antigravity to implement or correct the multicriteria inventory-classification capability:",
        s["B"]
    )]
    prompt_table = Table([[text_flow(d["classification_prompt"], s["B"])]], colWidths=[6.8*inch])
    prompt_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),lb),
        ("BOX",(0,0),(-1,-1),.5,bd),
        ("PADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"TOP")
    ]))
    story += [prompt_table, Spacer(1,7)]

    story += [Paragraph("Test 1 - Portfolio Summary", s["H"])]
    rows=[["Final Class","Item Count","Total Sales"]]+[
        [f"Class {c}", str(d[c+"c"]), f'${d[c+"s"]:,.2f}'] for c in "ABCD"
    ]
    t=Table(rows,colWidths=[2.2*inch,1.7*inch,2.4*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),navy),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BOX",(0,0),(-1,-1),.5,bd),
        ("INNERGRID",(0,0),(-1,-1),.3,bd),("FONTSIZE",(0,0),(-1,-1),9),
        ("PADDING",(0,0),(-1,-1),6)
    ]))
    story += [t, Spacer(1,7)]

    story += [Paragraph("Test 2 - Top 5 Items by Sales for Each Final Class", s["H"])]
    rows = [["Rank", "Class A", "Class B", "Class C", "Class D"]]
    for i in range(5):
        rows.append([
            str(i+1),
            esc(d["top_items"]["A"][i]),
            esc(d["top_items"]["B"][i]),
            esc(d["top_items"]["C"][i]),
            esc(d["top_items"]["D"][i]),
        ])
    t=Table(rows, colWidths=[0.55*inch,1.45*inch,1.45*inch,1.45*inch,1.45*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),teal),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BOX",(0,0),(-1,-1),.5,bd),
        ("INNERGRID",(0,0),(-1,-1),.3,bd),("PADDING",(0,0),(-1,-1),6)
    ]))
    story += [t, Spacer(1,7)]

    story += [Paragraph("Item 1170 Classification Check", s["H"])]
    rows=[
        ["Measure","Reported Result"],
        ["Sales Class",d["sc"]],
        ["Hits Class",d["hc"]],
        ["Combined Score",d["score"]],
        ["Final Inventory Class",d["fc"]],
    ]
    t=Table(rows,colWidths=[2.5*inch,3*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),navy),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BOX",(0,0),(-1,-1),.5,bd),
        ("INNERGRID",(0,0),(-1,-1),.3,bd),("PADDING",(0,0),(-1,-1),6)
    ]))
    story += [t, PageBreak()]

    story += [Paragraph("Part 2 - Inventory Policy: Student Analysis", s["H"])]
    story += [Paragraph(
        "The responses in this section are the student's own analysis based on the inventory concepts covered in the course.",
        s["B"]
    )]
    for (title,q),ans in zip(POLICY_QUESTIONS,d["policy"]):
        story += [Paragraph(title,s["H"])]
        qb=Table([[Paragraph("<b>Question</b><br/>"+esc(q),s["B"])]],colWidths=[6.8*inch])
        qb.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),lb),("BOX",(0,0),(-1,-1),.5,bd),
            ("PADDING",(0,0),(-1,-1),7)
        ]))
        story += [qb,Spacer(1,4),Paragraph("<b>Student Answer</b>",s["B"])]
        rb=Table([[text_flow(ans,s["B"])]],colWidths=[6.8*inch])
        rb.setStyle(TableStyle([
            ("BOX",(0,0),(-1,-1),.5,bd),("PADDING",(0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"TOP")
        ]))
        story += [rb,Spacer(1,7)]

    story += [PageBreak(), Paragraph("Part 3 - Inventory Decision Agent Validation", s["H"])]
    story += [Paragraph(
        "For each test below, the student entered the prompt into the final deployed Inventory Decision Agent, reviewed the result, and pasted the final agent response.",
        s["B"]
    )]
    for (title,prompt),ans in zip(AUDIT_PROMPTS,d["audit"]):
        story += [Paragraph(title,s["H"])]
        pb=Table([[Paragraph("<b>Prompt</b><br/>"+esc(prompt),s["B"])]],colWidths=[6.8*inch])
        pb.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),lb),("BOX",(0,0),(-1,-1),.5,bd),
            ("PADDING",(0,0),(-1,-1),7)
        ]))
        story += [pb,Spacer(1,4),Paragraph("<b>Final Agent Response</b>",s["B"])]
        rb=Table([[text_flow(ans,s["B"])]],colWidths=[6.8*inch])
        rb.setStyle(TableStyle([
            ("BOX",(0,0),(-1,-1),.5,bd),("PADDING",(0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"TOP")
        ]))
        story += [rb,Spacer(1,7)]

    story += [PageBreak(), Paragraph("Student Certification",s["H"])]
    certs=[
        "I confirm that the inventory-classification prompt included in this report is the final prompt I used to implement or correct the classification capability in my submitted application.",
        "I confirm that the classification results entered in this report were obtained from the final classification output produced by the Streamlit Inventory Analytics Agent that I developed and deployed for this project.",
        "I confirm that the answers in the Inventory Policy section are my own analysis based on the inventory concepts covered in this course.",
        "I confirm that the Inventory Decision Agent responses entered in this report were generated by the final version of my deployed application.",
        "I confirm that I reviewed the classifications, calculations, units, assumptions, and recommendations and corrected my application where necessary before generating this report."
    ]
    for c in certs:
        story += [Paragraph("<b>Confirmed:</b> "+esc(c),s["B"]),Spacer(1,3)]
    story += [Spacer(1,6),Paragraph("<b>Certified by:</b> "+esc(d["name"]),s["B"])]
    story += [Paragraph(
        "This report generator records student-entered classification results, student analysis, and final agent responses. It does not independently determine analytical correctness.",
        s["S"]
    )]

    def footer(c,docobj):
        c.saveState(); c.setFont("Helvetica",7.5); c.setFillColor(colors.grey)
        c.drawString(.62*inch,.32*inch,COURSE)
        c.drawRightString(letter[0]-.62*inch,.32*inch,f'{d["rid"]} | Page {docobj.page}')
        c.restoreState()

    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    out=buf.getvalue(); buf.close(); return out

st.markdown("""
<style>
.block-container{max-width:1050px;padding-top:2rem;padding-bottom:4rem}
.prompt{background:#eef7ff;border-left:5px solid #3b82b8;border-radius:8px;padding:12px 15px;margin:8px 0 10px}
.note{background:#f4fbfb;border-left:5px solid #008c95;border-radius:8px;padding:12px 15px;margin-bottom:16px}
</style>
""",unsafe_allow_html=True)

st.title("Inventory Agent Project Report Generator")
st.caption(COURSE)
st.markdown("""
<div class="note">
<b>Complete this report only after you have finished testing and correcting your Inventory Analytics Agent.</b><br>
Part 1 records the portfolio summary and Top 5 items by Sales for each final inventory class from your application's classification output. Part 2 contains your own inventory-policy analysis. Part 3 records responses generated by your final Inventory Decision Agent.
</div>
""",unsafe_allow_html=True)

c1,c2=st.columns([1,2])
with c1:
    name=st.text_input("Student Name",placeholder="Enter your full name")
with c2:
    url=st.text_input("Deployed Inventory Agent URL",placeholder="https://your-agent.streamlit.app")

st.divider()
st.header("Part 1 - Multicriteria Inventory Classification Results")
st.caption("Read these results directly from the classification output/table produced by your final Streamlit application.")

st.subheader("Final Inventory Classification Prompt")
st.caption(
    "Paste the final prompt you used in Antigravity to implement or correct the multicriteria "
    "inventory-classification capability. Enter your final prompt, not the original starter prompt provided in the assignment."
)
classification_prompt = st.text_area(
    "Final Antigravity Prompt",
    height=260,
    placeholder="Paste your final inventory-classification prompt here.",
    key="classification_prompt"
)

st.subheader("Test 1 - Portfolio Summary")
st.write("Enter the number of items and total Sales for each final inventory class.")
vals={}
for col,c in zip(st.columns(4),"ABCD"):
    with col:
        vals[c+"c"]=st.number_input(f"Class {c} Item Count",min_value=0,step=1,key=f"{c}c")
        vals[c+"s"]=st.number_input(f"Class {c} Total Sales ($)",min_value=0.0,step=0.01,format="%.2f",key=f"{c}s")

st.subheader("Test 2 - Top 5 Items by Sales for Each Final Class")
st.caption("From the classification output, enter the five highest-Sales Item Numbers for each final inventory class, ranked from highest to lowest Sales.")
top_items = {}
for c in "ABCD":
    st.markdown(f"**Class {c}**")
    entries = []
    for i, col in enumerate(st.columns(5), 1):
        with col:
            entries.append(
                st.text_input(
                    f"Class {c} Rank {i}",
                    placeholder="Item Number",
                    key=f"top_{c}_{i}"
                )
            )
    top_items[c] = entries

st.subheader("Item 1170 Classification Check")
c1,c2=st.columns(2)
with c1:
    sc=st.text_input("Sales Class")
    hc=st.text_input("Hits Class")
with c2:
    score=st.text_input("Combined Score")
    fc=st.text_input("Final Inventory Class")

st.divider()
st.header("Part 2 - Inventory Policy: Your Analysis")
st.caption("Answer these questions yourself using the inventory concepts covered in the module. Do not ask your agent to write these answers.")

policy=[]
for i,(title,q) in enumerate(POLICY_QUESTIONS,4):
    st.subheader(title)
    st.markdown(f'<div class="prompt"><b>Question</b><br>{esc(q)}</div>',unsafe_allow_html=True)
    policy.append(st.text_area(
        "Your Answer",
        height=180,
        key=f"policy_{i}",
        placeholder="Enter your own analysis here."
    ))

st.divider()
st.header("Part 3 - Inventory Decision Agent Validation")
st.caption("Enter each prompt exactly as shown into your final deployed agent. Review the result, then paste the complete final agent response.")

audit=[]
for i,(title,prompt) in enumerate(AUDIT_PROMPTS,6):
    st.subheader(title)
    st.markdown(f'<div class="prompt"><b>Prompt</b><br>{esc(prompt)}</div>',unsafe_allow_html=True)
    audit.append(st.text_area(
        "Paste the final agent response",
        height=240,
        key=f"audit_{i}",
        placeholder="Paste the complete final response here."
    ))

st.divider()
st.header("Student Certification")
cert0=st.checkbox("I confirm that the inventory-classification prompt included in this report is the final prompt I used to implement or correct the classification capability in my submitted application.")
cert1=st.checkbox("I confirm that the classification results entered in this report were obtained from the final classification output produced by the Streamlit Inventory Analytics Agent that I developed and deployed for this project.")
cert2=st.checkbox("I confirm that the answers in the Inventory Policy section are my own analysis based on the inventory concepts covered in this course.")
cert3=st.checkbox("I confirm that the Inventory Decision Agent responses entered in this report were generated by the final version of my deployed application.")
cert4=st.checkbox("I confirm that I reviewed the classifications, calculations, units, assumptions, and recommendations and corrected my application where necessary before generating this report.")

missing = not (
    name.strip() and url.strip()
    and classification_prompt.strip()
    and all(x.strip() for c in "ABCD" for x in top_items[c])
    and sc.strip() and hc.strip() and score.strip() and fc.strip()
    and all(x.strip() for x in policy)
    and all(x.strip() for x in audit)
    and cert0 and cert1 and cert2 and cert3 and cert4
)

if st.button("Generate Project Verification Report",type="primary",disabled=missing):
    ts=datetime.now().astimezone().strftime("%B %d, %Y at %I:%M %p %Z")
    reportid=make_id(name,url,ts)
    d={
        "name":name.strip(),"url":url.strip(),"ts":ts,"rid":reportid,
        **vals,
        "classification_prompt": classification_prompt.strip(),
        "top_items": {c: [x.strip() for x in top_items[c]] for c in "ABCD"},
        "sc":sc.strip(),"hc":hc.strip(),"score":score.strip(),"fc":fc.strip(),
        "policy":[x.strip() for x in policy],
        "audit":[x.strip() for x in audit]
    }
    st.session_state["pdf"]=build_pdf(d)
    st.session_state["fn"]=re.sub(r"[^A-Za-z0-9_-]+","_",name.strip()).strip("_")
    st.session_state["reportid"]=reportid
    st.success(f"Report generated. Report ID: {reportid}")

if "pdf" in st.session_state:
    st.download_button(
        "Download Project Verification Report (PDF)",
        st.session_state["pdf"],
        file_name=f'BAN517_Inventory_Agent_Report_{st.session_state["fn"]}.pdf',
        mime="application/pdf"
    )
