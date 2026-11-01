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

COURSE="BAN 517: Supply Chain Analytics"
PROJECT="Inventory Analytics Agent Project"

POLICY_PROMPTS=[
("Test 5 - Class A Inventory Policy","What inventory-management policy would you recommend for Class A inventory?"),
("Test 6 - Apply Policy to the Portfolio","Show the top 5 Class A items by Sales and include the recommended inventory-management policy for these items.")
]
AUDIT_PROMPTS=[
("Test 7 - EOQ","Find EOQ. Demand is 1,000 units per month, ordering cost is $25 per order, and holding cost is $0.50 per unit per year."),
("Test 8 - Safety Stock and Reorder Point","A product has average demand of 40 units per day with a standard deviation of 8 units per day. Average lead time is 3 weeks with a standard deviation of 0.5 weeks. Determine the safety stock and reorder point for a 95% service level."),
("Test 9 - Quantity Discount","Annual demand is 5,000 units. Ordering cost is $60 per order and annual holding cost is 20% of unit cost. The supplier charges $12 per unit for orders below 500 units, $11.50 for 500-999 units, and $11 for orders of 1,000 units or more. Find the best order quantity and annual cost.")
]

def esc(x):
    return str(x or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def rid(name,url,ts):
    raw=f"{name}|{url}|{ts}|{secrets.token_hex(4)}".encode()
    return "INV-"+hashlib.sha256(raw).hexdigest()[:12].upper()

def paras(text,style):
    out=[]
    for b in re.split(r"\n\s*\n",str(text or "").strip()):
        if b.strip():
            out += [Paragraph(esc(b).replace("\n","<br/>"),style),Spacer(1,4)]
    return out

def build_pdf(d):
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=letter,leftMargin=.62*inch,rightMargin=.62*inch,topMargin=.58*inch,bottomMargin=.58*inch)
    s=getSampleStyleSheet(); navy=colors.HexColor("#003B5C"); teal=colors.HexColor("#006C67"); lt=colors.HexColor("#F4FBFB"); lb=colors.HexColor("#EEF7FF"); bd=colors.HexColor("#D7E0E8")
    s.add(ParagraphStyle(name="T",parent=s["Title"],fontName="Helvetica-Bold",fontSize=18,leading=22,textColor=navy,alignment=TA_CENTER))
    s.add(ParagraphStyle(name="H",parent=s["Heading2"],fontName="Helvetica-Bold",fontSize=12,leading=15,textColor=navy,spaceBefore=9,spaceAfter=6))
    s.add(ParagraphStyle(name="B",parent=s["BodyText"],fontSize=9.2,leading=13,textColor=colors.HexColor("#0B2239"),spaceAfter=4))
    s.add(ParagraphStyle(name="S",parent=s["BodyText"],fontSize=7.8,leading=10,textColor=colors.HexColor("#5D6B78")))
    story=[Paragraph(PROJECT,s["T"]),Paragraph(COURSE+" | Project Verification Report",s["B"]),Spacer(1,7)]
    meta=[["Student",esc(d["name"])],["Deployed Inventory Agent",esc(d["url"])],["Generated",d["ts"]],["Report ID",d["rid"]]]
    t=Table(meta,colWidths=[1.65*inch,5.15*inch]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),lb),("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("BOX",(0,0),(-1,-1),.5,bd),("INNERGRID",(0,0),(-1,-1),.3,bd),("FONTSIZE",(0,0),(-1,-1),8.3),("PADDING",(0,0),(-1,-1),6)])); story += [t,Spacer(1,8)]

    story += [Paragraph("Part 1 - Multicriteria Inventory Classification Results",s["H"])]
    story += [Paragraph("These values were transcribed by the student from the final classification output produced by the deployed Streamlit application.",s["B"])]
    rows=[["Final Class","Item Count","Total Sales"]]+[[f"Class {c}",str(d[c+"c"]),f'${d[c+"s"]:,.2f}'] for c in "ABCD"]
    t=Table(rows,colWidths=[2.2*inch,1.7*inch,2.4*inch]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),navy),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BOX",(0,0),(-1,-1),.5,bd),("INNERGRID",(0,0),(-1,-1),.3,bd),("FONTSIZE",(0,0),(-1,-1),9),("PADDING",(0,0),(-1,-1),6)])); story += [t,Spacer(1,7)]
    story += [Paragraph("Test 2 - Class A Inventory",s["H"]),Paragraph("<b>Class A Item Numbers:</b> "+esc(d["aitems"]),s["B"])]
    story += [Paragraph("Test 3 - Top 5 Class A Items by Sales",s["H"])]
    t=Table([["Rank","Item Number"]]+[[str(i+1),esc(x)] for i,x in enumerate(d["top5"])],colWidths=[1*inch,3*inch]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),teal),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BOX",(0,0),(-1,-1),.5,bd),("INNERGRID",(0,0),(-1,-1),.3,bd),("PADDING",(0,0),(-1,-1),6)])); story += [t]
    story += [Paragraph("Test 4 - Item 1170 Classification",s["H"])]
    rows=[["Measure","Reported Result"],["Sales Class",d["sc"]],["Hits Class",d["hc"]],["Combined Score",d["score"]],["Final Inventory Class",d["fc"]]]
    t=Table(rows,colWidths=[2.5*inch,3*inch]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),navy),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BOX",(0,0),(-1,-1),.5,bd),("INNERGRID",(0,0),(-1,-1),.3,bd),("PADDING",(0,0),(-1,-1),6)])); story += [t,PageBreak()]

    story += [Paragraph("Part 2 - Inventory Policy",s["H"])]
    for (title,prompt),ans in zip(POLICY_PROMPTS,d["policy"]):
        story += [Paragraph(title,s["H"])]
        pb=Table([[Paragraph("<b>Prompt</b><br/>"+esc(prompt),s["B"])]],colWidths=[6.8*inch]); pb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),lb),("BOX",(0,0),(-1,-1),.5,bd),("PADDING",(0,0),(-1,-1),7)])); story += [pb,Spacer(1,4),Paragraph("<b>Final Agent Response</b>",s["B"])]
        rb=Table([[paras(ans,s["B"])]],colWidths=[6.8*inch]); rb.setStyle(TableStyle([("BOX",(0,0),(-1,-1),.5,bd),("PADDING",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"TOP")])); story += [rb,Spacer(1,6)]

    story += [PageBreak(),Paragraph("Part 3 - Inventory Decision Agent Validation",s["H"])]
    for (title,prompt),ans in zip(AUDIT_PROMPTS,d["audit"]):
        story += [Paragraph(title,s["H"])]
        pb=Table([[Paragraph("<b>Prompt</b><br/>"+esc(prompt),s["B"])]],colWidths=[6.8*inch]); pb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),lb),("BOX",(0,0),(-1,-1),.5,bd),("PADDING",(0,0),(-1,-1),7)])); story += [pb,Spacer(1,4),Paragraph("<b>Final Agent Response</b>",s["B"])]
        rb=Table([[paras(ans,s["B"])]],colWidths=[6.8*inch]); rb.setStyle(TableStyle([("BOX",(0,0),(-1,-1),.5,bd),("PADDING",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"TOP")])); story += [rb,Spacer(1,6)]

    story += [PageBreak(),Paragraph("Student Certification",s["H"])]
    certs=[
    "I confirm that the classification results entered in this report were obtained from the final classification output produced by the Streamlit Inventory Analytics Agent that I developed and deployed for this project.",
    "I confirm that the agent responses entered in this report were generated by the final version of that same deployed application.",
    "I confirm that I reviewed the classifications, calculations, units, assumptions, and recommendations using the inventory analytics methods covered in this course and corrected my application where necessary before generating this report."
    ]
    for c in certs: story += [Paragraph("<b>Confirmed:</b> "+esc(c),s["B"]),Spacer(1,3)]
    story += [Spacer(1,6),Paragraph("<b>Certified by:</b> "+esc(d["name"]),s["B"]),Paragraph("This report generator records student-entered results and final agent responses. It does not independently determine analytical correctness.",s["S"])]

    def footer(c,docobj):
        c.saveState(); c.setFont("Helvetica",7.5); c.setFillColor(colors.grey); c.drawString(.62*inch,.32*inch,COURSE); c.drawRightString(letter[0]-.62*inch,.32*inch,f'{d["rid"]} | Page {docobj.page}'); c.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    out=buf.getvalue(); buf.close(); return out

st.markdown("""<style>.block-container{max-width:1050px;padding-top:2rem;padding-bottom:4rem}.prompt{background:#eef7ff;border-left:5px solid #3b82b8;border-radius:8px;padding:12px 15px;margin:8px 0 10px}.note{background:#f4fbfb;border-left:5px solid #008c95;border-radius:8px;padding:12px 15px;margin-bottom:16px}</style>""",unsafe_allow_html=True)
st.title("Inventory Agent Project Report Generator")
st.caption(COURSE)
st.markdown("""<div class="note"><b>Complete this report only after you have finished testing and correcting your Inventory Analytics Agent.</b><br>
For Tests 1-4, read the requested values directly from the classification results produced by your final Streamlit application. For Tests 5-9, run the displayed prompt in your final agent and paste its complete final response.</div>""",unsafe_allow_html=True)

c1,c2=st.columns([1,2])
with c1: name=st.text_input("Student Name",placeholder="Enter your full name")
with c2: url=st.text_input("Deployed Inventory Agent URL",placeholder="https://your-agent.streamlit.app")

st.divider(); st.header("Part 1 - Multicriteria Inventory Classification Results")
st.caption("Do not ask the agent to answer Tests 1-4. Read these results from the classification output/table produced by your final application.")

st.subheader("Test 1 - Portfolio Summary")
st.write("Enter the number of items and total Sales shown for each final inventory class.")
vals={}
for col,c in zip(st.columns(4),"ABCD"):
    with col:
        vals[c+"c"]=st.number_input(f"Class {c} Item Count",min_value=0,step=1,key=f"{c}c")
        vals[c+"s"]=st.number_input(f"Class {c} Total Sales ($)",min_value=0.0,step=0.01,format="%.2f",key=f"{c}s")

st.subheader("Test 2 - Class A Inventory")
aitems=st.text_area("Class A Item Numbers",height=130,placeholder="Enter the Item Numbers classified as A, separated by commas.")

st.subheader("Test 3 - Top 5 Class A Items by Sales")
top5=[]
for i,col in enumerate(st.columns(5),1):
    with col: top5.append(st.text_input(f"Rank {i}",placeholder="Item Number",key=f"top{i}"))

st.subheader("Test 4 - Item 1170 Classification")
c1,c2=st.columns(2)
with c1:
    sc=st.text_input("Sales Class"); hc=st.text_input("Hits Class")
with c2:
    score=st.text_input("Combined Score"); fc=st.text_input("Final Inventory Class")

st.divider(); st.header("Part 2 - Inventory Policy")
st.caption("Run each prompt in your final deployed Inventory Analytics Agent and paste the complete final response.")
policy=[]
for i,(title,prompt) in enumerate(POLICY_PROMPTS,5):
    st.subheader(title); st.markdown(f'<div class="prompt"><b>Prompt</b><br>{esc(prompt)}</div>',unsafe_allow_html=True)
    policy.append(st.text_area("Paste the final agent response",height=190,key=f"p{i}"))

st.divider(); st.header("Part 3 - Inventory Decision Agent Validation")
st.caption("Run each prompt exactly as shown. Review the calculations, units, assumptions, and recommendation before entering the final response.")
audit=[]
for i,(title,prompt) in enumerate(AUDIT_PROMPTS,7):
    st.subheader(title); st.markdown(f'<div class="prompt"><b>Prompt</b><br>{esc(prompt)}</div>',unsafe_allow_html=True)
    audit.append(st.text_area("Paste the final agent response",height=240,key=f"a{i}"))

st.divider(); st.header("Student Certification")
cert1=st.checkbox("I confirm that the classification results entered in this report were obtained from the final classification output produced by the Streamlit Inventory Analytics Agent that I developed and deployed for this project.")
cert2=st.checkbox("I confirm that the agent responses entered in this report were generated by the final version of that same deployed application.")
cert3=st.checkbox("I confirm that I reviewed the classifications, calculations, units, assumptions, and recommendations using the inventory analytics methods covered in this course and corrected my application where necessary before generating this report.")

missing=not(name.strip() and url.strip() and aitems.strip() and all(x.strip() for x in top5) and sc.strip() and hc.strip() and score.strip() and fc.strip() and all(x.strip() for x in policy+audit) and cert1 and cert2 and cert3)
if st.button("Generate Project Verification Report",type="primary",disabled=missing):
    ts=datetime.now().astimezone().strftime("%B %d, %Y at %I:%M %p %Z"); reportid=rid(name,url,ts)
    d={"name":name.strip(),"url":url.strip(),"ts":ts,"rid":reportid,**vals,"aitems":aitems.strip(),"top5":[x.strip() for x in top5],"sc":sc.strip(),"hc":hc.strip(),"score":score.strip(),"fc":fc.strip(),"policy":[x.strip() for x in policy],"audit":[x.strip() for x in audit]}
    st.session_state["pdf"]=build_pdf(d); st.session_state["fn"]=re.sub(r"[^A-Za-z0-9_-]+","_",name.strip()).strip("_"); st.session_state["reportid"]=reportid
    st.success(f"Report generated. Report ID: {reportid}")
if "pdf" in st.session_state:
    st.download_button("Download Project Verification Report (PDF)",st.session_state["pdf"],file_name=f'BAN517_Inventory_Agent_Report_{st.session_state["fn"]}.pdf',mime="application/pdf")
