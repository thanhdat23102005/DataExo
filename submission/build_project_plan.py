"""
Generate the Practical Assessment Project Plan (Week 8, 20%).

Section order follows the marking rubric exactly, so a marker can score it
top to bottom: Project Background (3%), Detailed Analysis of Requirements
(10%), Clear Definition of Project Goals (10%), Methodology and Standards
(20%), plus the costings / resourcing / timeline / implementation /
evaluation content the assessment description asks for. The background
section embeds the block diagram, which the rubric requires for the top
band.

Bracketed [placeholders] are things only the student or teacher can fill in.

Usage:
    python3 build_project_plan.py
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

BLUE = RGBColor(0x1F, 0x3A, 0x5F)
ASSETS = Path(__file__).parent / "assets"


def set_cell_shading(cell, hex_color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shd)


def base_doc():
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    for section in doc.sections:
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)
    return doc


def h1(doc, text):
    p = doc.add_heading(text, level=1)
    p.runs[0].font.color.rgb = BLUE
    return p


def h2(doc, text):
    p = doc.add_heading(text, level=2)
    p.runs[0].font.color.rgb = BLUE
    return p


def body(doc, text):
    return doc.add_paragraph(text)


def bullets(doc, items):
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    for i, head in enumerate(headers):
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(head)
        run.bold = True
        run.font.size = Pt(10)
        set_cell_shading(hdr[i], "DCE6F1")
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(val))
            run.font.size = Pt(10)
    return t


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(9)
    return p


def build():
    doc = base_doc()

    # ---------------- Cover ----------------
    title = doc.add_heading("DataExodus", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.runs[0].font.color.rgb = BLUE

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run("Practical Assessment — Project Plan")
    run.bold = True
    run.font.size = Pt(14)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run(
        "Making cross-border tracking and hashed-identifier leakage visible,\n"
        "then blocking it at the network edge"
    ).italic = True

    doc.add_paragraph()
    table(doc, ["Field", "Detail"], [
        ["Student", "Thanh Dat Phan"],
        ["Student ID", "[Student ID]"],
        ["Unit", "[Unit code and name]"],
        ["Assessor", "[Unit Teacher / Course Coordinator]"],
        ["Submission", "Week 8 — Moodle, 5:00 pm AEST"],
        ["Repository", "github.com/thanhdat23102005/DataExo"],
    ])

    doc.add_page_break()

    # ============================================================
    # 1. PROJECT BACKGROUND  (3%)
    # ============================================================
    h1(doc, "1. Project Background")

    body(doc,
         "Open the developer tools on almost any Australian news or government site and the page "
         "contacts a dozen companies the visitor has never heard of. The Australian Competition and "
         "Consumer Commission's Digital Platforms Inquiry found that consumers have little practical "
         "visibility of this, and the Privacy Act's Australian Privacy Principle 8 places obligations "
         "on organisations that disclose personal information overseas. Neither the visibility nor the "
         "accountability is easy for an individual to check for themselves.")

    body(doc,
         "The specific claim this project tests is that hashing an identifier makes it anonymous. It "
         "does not. Because the same email address always produces the same hash, that hash is a "
         "stable name for a person that can be matched across unrelated websites, even though the raw "
         "address never crosses the wire. The United States Federal Trade Commission issued guidance "
         "in 2024 making the same point. A system that hashes a user's own identifier locally and then "
         "watches for those hashes in outbound traffic can demonstrate the weakness directly, rather "
         "than describing it.")

    body(doc,
         "The project was initiated by the student as an individual undertaking for this unit. There "
         "is no external sponsor or client; the assessor acts as the approving stakeholder. It fits the "
         "unit's project criteria because it is a complex technology project rather than a single "
         "artefact: it combines applied research, software built across two platforms, a measurement "
         "study with stated hypotheses, and a deployment that has to work on real hardware in a real "
         "home network.")

    body(doc,
         "The deliverables are deliberately two things a person can install. A Chrome extension makes "
         "the problem visible on one machine. A Raspberry Pi 5 application collects what the extension "
         "observes, adds attribution the browser cannot perform, and blocks tracker domains by DNS for "
         "every device on the network, including phones and televisions no browser extension can reach.")

    diagram = ASSETS / "architecture_block_diagram.png"
    if diagram.exists():
        doc.add_picture(str(diagram), width=Inches(6.4))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption(doc, "Figure 1 — System architecture block diagram: components, data flows, "
                     "and the privacy boundary that raw identifiers and page URLs never cross.")

    # ============================================================
    # 2. REQUIREMENTS  (10%)
    # ============================================================
    h1(doc, "2. Detailed Analysis of Requirements")

    body(doc,
         "Requirements were derived from three sources: the research question itself, the legal context "
         "of APP 8, and the practical constraints of the platforms involved. They are recorded here, "
         "carry stable identifiers, and are traced through to verification in Table 4 so that nothing "
         "is claimed without a way to check it.")

    h2(doc, "2.1 High-level requirements — what needs to be done")
    table(doc, ["ID", "Requirement", "Rationale"], [
        ["HR-1", "Identify who receives data from a visited page, and which company owns them",
         "Attribution is the basis of every other finding"],
        ["HR-2", "Determine the destination country and flag transfers outside comparable regimes",
         "Directly addresses APP 8 cross-border disclosure"],
        ["HR-3", "Detect the user's own identifier leaving as a hash, not only in plain text",
         "The project's central claim about anonymisation"],
        ["HR-4", "Distinguish covert disclosure to third parties from intentional first-party use",
         "Without this, ordinary use of a search box reads as a breach"],
        ["HR-5", "Block tracker domains for every device on the network, not only one browser",
         "Phones, televisions and apps cannot run an extension"],
        ["HR-6", "Present findings so a non-specialist can act on them",
         "A finding nobody understands changes nothing"],
        ["HR-7", "Measure tracking across a defined sample of Australian sites",
         "Supports the research hypotheses H1–H4"],
    ])

    doc.add_paragraph()
    h2(doc, "2.2 Low-level requirements — how it will be done")
    table(doc, ["ID", "Requirement", "Implementation approach"], [
        ["LR-1", "Capture every outbound request in the browser",
         "Chrome Manifest V3 service worker, webRequest observer"],
        ["LR-2", "Hash the identifier locally across every plausible normalisation",
         "WebCrypto SHA-1/256/512 plus a local MD5; digits-only, +61, 61, Gmail dot and +tag forms"],
        ["LR-3", "Never transmit the raw identifier or full page URLs",
         "Only hostnames, risk scores and hash-match events are sent"],
        ["LR-4", "Resolve destination hostnames to a country",
         "MaxMind GeoLite2 lookup on the Pi, where the database can be held in memory"],
        ["LR-5", "Store observations idempotently",
         "DuckDB upsert keyed on (tab, destination); retried deliveries must not double-count"],
        ["LR-6", "Answer tracker DNS queries with 0.0.0.0 and forward everything else",
         "Threaded UDP server using dnslib, upstream 1.1.1.1"],
        ["LR-7", "Keep blocking decisions separate from labelling decisions",
         "Hosts-format list for DNS; EasyPrivacy whole-domain rules for labelling"],
        ["LR-8", "Provide a dashboard and an in-browser popup",
         "FastAPI-served dashboard polling a summary endpoint; extension popup"],
        ["LR-9", "Crawl the study sample reproducibly",
         "Playwright headless crawler over a site list frozen in week 1"],
    ])

    # ============================================================
    # 3. GOALS  (10%)
    # ============================================================
    doc.add_page_break()
    h1(doc, "3. Definition of Project Goals")

    body(doc,
         "Each goal is specific, measurable, achievable, results-oriented and time-bound, and together "
         "they cover every requirement listed above.")

    table(doc, ["Goal", "SMART statement", "Covers"], [
        ["G1", "By week 10, correctly attribute owner and country for at least 90% of third-party "
               "destinations observed on the study sample, verified by manual spot-check against "
               "Tracker Radar.", "HR-1, HR-2"],
        ["G2", "By week 10, demonstrate a hashed identifier being matched in live traffic across at "
               "least four hash algorithms and four normalisation forms, evidenced by a reproducible "
               "test.", "HR-3"],
        ["G3", "By week 11, classify every identifier match as covert or intentional with zero "
               "misclassification across the manual test set.", "HR-4"],
        ["G4", "By week 11, block at least 75,000 tracker domains network-wide with zero false "
               "positives across a defined set of twelve common Australian and global sites.",
         "HR-5"],
        ["G5", "By week 12, present results through a browser popup and a Pi dashboard that a "
               "non-specialist can read without explanation, validated by one informal usability walk-"
               "through.", "HR-6"],
        ["G6", "By week 13, complete the 50-site crawl and report on hypotheses H1–H4 with stated "
               "statistical methods.", "HR-7"],
    ])

    # ============================================================
    # 4. METHODOLOGY AND STANDARDS  (20%)
    # ============================================================
    doc.add_page_break()
    h1(doc, "4. Methodology and Standards")

    h2(doc, "4.1 Development methodology and why")
    body(doc,
         "The project uses incremental delivery in vertical layers: each layer is a complete, working "
         "system on its own, and later layers add capability without the earlier ones becoming "
         "worthless. Layer one is the extension alone. Layer two adds the Pi collector. Layer three "
         "adds network-wide DNS blocking. Layer four is the measurement study.")

    body(doc,
         "This was chosen over a waterfall sequence because the riskiest unknowns are technical and "
         "sit early: whether Manifest V3 permits the necessary observation, and whether a DNS blocklist "
         "can be applied without breaking ordinary websites. A waterfall plan would surface those in "
         "an integration phase with no time left to respond. It was chosen over formal Scrum because "
         "ceremonies designed to coordinate a team add overhead without benefit for a single student; "
         "the useful parts of agile practice — short increments, working software at each step, "
         "revising the plan against evidence — are retained without the meeting structure.")

    body(doc,
         "The approach has already justified itself. A DNS blocklist parser written during layer three "
         "classified wikipedia.org and github.com as trackers, because rules that block a single path "
         "were read as blocking an entire domain. At the DNS layer that error removes a site from the "
         "network for every device, not for one browser. It was found by testing the layer in isolation "
         "before it was connected to anything, which a later integration phase would not have permitted.")

    h2(doc, "4.2 Tools and why each was selected")
    table(doc, ["Tool", "Used for", "Justification"], [
        ["Chrome Manifest V3", "Browser observation",
         "The only extension platform Chrome now accepts; forces an honest design because blocking "
         "webRequest is unavailable"],
        ["Python 3 + FastAPI", "Pi application",
         "Async HTTP with typed request handling; runs comfortably on a Pi 5 and is the language the "
         "analysis code already uses"],
        ["DuckDB", "Storage and analysis",
         "Columnar analytical queries in a single file with no server to administer; suits aggregate "
         "questions such as 'which owner receives the most requests'"],
        ["dnslib", "DNS sinkhole",
         "Pure Python, no system DNS server to configure, and the blocking logic stays readable and "
         "testable rather than hidden in dnsmasq configuration"],
        ["Playwright", "Study crawler",
         "Drives a real browser, so JavaScript-inserted trackers are captured as a real visitor would "
         "trigger them"],
        ["MaxMind GeoLite2", "Country attribution",
         "Free, offline, and widely cited in academic measurement work"],
        ["EasyPrivacy and DuckDuckGo Tracker Radar", "Tracker and owner identification",
         "Public and independently checkable, so any classification in this report can be audited"],
    ])

    doc.add_paragraph()
    h2(doc, "4.3 Standards applied")
    bullets(doc, [
        "Privacy Act 1988 (Cth), Australian Privacy Principle 8 — the definition of a cross-border "
        "disclosure used throughout; country adequacy is applied as a documented simplification, not "
        "as legal advice.",
        "Chrome Extensions Manifest V3 — required platform standard; the extension declares only the "
        "permissions it uses.",
        "Privacy by design — the raw identifier and full page URLs never leave the browser. Hashing is "
        "performed client-side and only hashes are ever compared.",
        "PEP 8 and type annotations for Python; ES modules for extension JavaScript.",
        "Semantic versioning on the extension manifest, so a demonstration can be tied to an exact build.",
        "Passive-observation research ethics, following published web-measurement practice such as "
        "Princeton's WebTAP: public pages only, no authentication, no attacks, no evasion, and only "
        "the student's own traffic and own identifier.",
    ])

    h2(doc, "4.4 Rule-based classification, and no machine learning in the core")
    body(doc,
         "Every classification in the core system is rule-based and traceable to a public list. This is "
         "a deliberate constraint rather than a limitation of skill: it means each of the study's "
         "results can be checked by hand, which is why the sample is fixed at 50 sites — a number small "
         "enough to audit rather than one large enough to sound impressive and impossible to verify. A "
         "separate exploratory module asks whether a lightweight model can recognise a tracker from "
         "request shape alone without consulting a blocklist. It is trained on the rule-based labels, "
         "reported separately, and does not contribute to the study's figures.")

    # ============================================================
    # 5. RESOURCES, STAFFING, COSTINGS
    # ============================================================
    doc.add_page_break()
    h1(doc, "5. Resources, Staffing and Costings")

    body(doc,
         "The project is staffed by one person. The roles below are distinct bodies of work rather than "
         "distinct people, and are listed separately because they carry different risks: an error in the "
         "classification role produces wrong findings, while an error in the deployment role takes a "
         "household off the internet.")

    table(doc, ["Role", "Responsibilities", "Effort (est.)"], [
        ["Developer", "Extension, Pi application, DNS sinkhole, crawler", "~70 h"],
        ["Data analyst", "Classification accuracy, hypothesis testing, reporting", "~25 h"],
        ["Deployment / test", "Pi setup, network configuration, false-positive testing", "~15 h"],
        ["Technical writer", "Charter, literature review, plan, presentations", "~20 h"],
    ])

    doc.add_paragraph()
    table(doc, ["Item", "Cost (AUD)", "Note"], [
        ["Raspberry Pi 5 (8 GB)", "~$145", "Already owned; listed at replacement cost"],
        ["Power supply, 64 GB microSD, case", "~$65", "Already owned"],
        ["Software — Python, FastAPI, DuckDB, Playwright, dnslib", "$0", "Open source"],
        ["EasyPrivacy, Tracker Radar, GeoLite2", "$0", "Free licences; GeoLite2 requires registration"],
        ["Grafana and InfluxDB (optional monitoring)", "$0", "Self-hosted open-source editions"],
        ["Total cash outlay for the project", "$0", "All hardware pre-owned, all software free"],
    ])

    body(doc,
         "The absence of licence cost is itself a design decision. Every data source is public, so the "
         "work can be reproduced by an assessor or another student without purchasing anything, which "
         "would not be true of a commercial threat-intelligence feed.")

    # ============================================================
    # 6. TIMELINE
    # ============================================================
    h1(doc, "6. Timeline and Milestones")

    table(doc, ["Week", "Milestone", "Status"], [
        ["1–3", "Topic definition, site list frozen, project charter", "Complete"],
        ["4–5", "Literature review; crawler and classification pipeline", "Complete"],
        ["6–7", "Extension: capture, risk scoring, local hashing, malware blocking", "Complete"],
        ["8", "Pi application, DNS sinkhole, project plan, early-stage presentation", "This submission"],
        ["9–10", "Full 50-site crawl; owner and country attribution measured against G1, G2", "Planned"],
        ["11", "Network deployment and false-positive testing against G3, G4", "Planned"],
        ["12", "Dashboard refinement and usability walk-through (G5)", "Planned"],
        ["13", "Hypothesis testing and written report (G6)", "Planned"],
        ["14", "Final presentation and submission", "Planned"],
    ])

    # ============================================================
    # 7. IMPLEMENTATION
    # ============================================================
    h1(doc, "7. Implementation Details")

    body(doc,
         "Work to date is not a prototype sketch. The following is implemented and has been executed "
         "end to end, which is the evidence behind the status column above.")

    table(doc, ["Component", "State", "Evidence"], [
        ["Extension (Manifest V3)", "Built, v3.3",
         "Captures requests, hashes locally, scores risk, blocks malware domains"],
        ["Local MD5 implementation", "Verified",
         "Matches a reference implementation on 12 test vectors including UTF-8 input and the 55/56/57/"
         "64-byte padding boundaries"],
        ["Identifier normalisation", "Verified",
         "An identifier typed as '0412 345 678' is matched when a tracker hashes '61412345678'; the "
         "single-form approach it replaced did not match"],
        ["Pi telemetry API", "Built and tested",
         "A retried delivery produces no duplicate rows and no double-counted requests"],
        ["DNS sinkhole", "Built and tested",
         "Blocked domains answer 0.0.0.0 and :: ; unrelated domains are forwarded; zero false positives "
         "across the twelve-site test set"],
        ["Pi dashboard", "Built", "Owners, countries, offshore flags, identifier events, DNS blocks"],
        ["Study crawler and pipeline", "Built, sample run",
         "10 government sites crawled; 543 requests classified into the database"],
    ])

    doc.add_paragraph()
    body(doc,
         "Two items are known to be outstanding and are scheduled rather than hidden. Three unit-test "
         "files in the research track fail at import because they were written against an earlier "
         "module interface, and the remaining forty sites have not yet been crawled. Both are addressed "
         "in weeks 9 and 10.")

    # ============================================================
    # 8. EVALUATION
    # ============================================================
    h1(doc, "8. How the Project Will Be Evaluated")

    body(doc,
         "Evaluation is against the goals in section 3, using evidence that can be reproduced by "
         "someone else rather than asserted.")

    table(doc, ["Goal", "Method of evaluation", "Pass condition"], [
        ["G1", "Manual spot-check of attribution against Tracker Radar for a random sample of 30 "
               "destinations", "≥ 90% agreement"],
        ["G2", "Scripted test hashing a known identifier in four forms and four algorithms, then "
               "matching against synthetic traffic", "All forms matched"],
        ["G3", "Manual test set of first-party and third-party identifier transmissions",
         "Zero misclassification"],
        ["G4", "Automated block/allow test over twelve named sites plus normal browsing for one week",
         "Zero false positives; ≥ 75,000 domains loaded"],
        ["G5", "Usability walk-through with one non-technical participant, structured think-aloud",
         "Participant states correctly who collected their data and where it went"],
        ["G6", "Kruskal–Wallis for H1, H2 and H4 across sectors; proportion with confidence interval "
               "for H3", "Result reported with method and effect size, significant or not"],
    ])

    doc.add_paragraph()
    body(doc,
         "A negative result is still a result. If tracking density does not differ by sector, that is "
         "reported as found; the project is not designed to confirm a preferred conclusion.")

    # ============================================================
    # 9. RISKS
    # ============================================================
    h1(doc, "9. Risks and Mitigation")

    table(doc, ["Risk", "Impact", "Mitigation"], [
        ["A blocklist false positive removes a site for the whole household",
         "High", "Blocking and labelling use separate sources; a defined allow-test runs before "
                 "deployment; documented rollback of router DNS"],
        ["The Pi becomes a single point of DNS failure", "High",
         "Documented revert procedure; secondary DNS deliberately left blank is a stated trade-off, "
         "not an oversight"],
        ["Chrome DNS-over-HTTPS bypasses the sinkhole", "Medium",
         "Documented as a limitation; the extension still observes these requests, which is why both "
         "deliverables exist"],
        ["Sites change during the study period", "Medium",
         "Site list frozen in week 1; crawl dates recorded with results"],
        ["Crawling from a single network biases attribution", "Medium",
         "Stated as a limitation; GeoIP reports where a server is, not where data is ultimately stored"],
        ["Scope growth beyond available time", "Medium",
         "Layered delivery: each layer is independently demonstrable, so later layers can be cut "
         "without invalidating earlier ones"],
    ])

    # ============================================================
    # 10. REFERENCES
    # ============================================================
    h1(doc, "10. References")
    bullets(doc, [
        "Australian Competition and Consumer Commission 2019, Digital Platforms Inquiry — Final Report, ACCC, Canberra.",
        "Attorney-General's Department 2022, Privacy Act Review — Report, Commonwealth of Australia.",
        "Federal Trade Commission 2024, 'Hashing is not anonymization', FTC Technology Blog.",
        "Englehardt, S & Narayanan, A 2016, 'Online tracking: a 1-million-site measurement and analysis', "
        "Proceedings of the ACM SIGSAC Conference on Computer and Communications Security.",
        "Office of the Australian Information Commissioner, Australian Privacy Principles Guidelines, Chapter 8.",
        "DuckDuckGo 2024, Tracker Radar dataset; EasyList project, EasyPrivacy filter list.",
    ])

    out = Path(__file__).parent / "Project_Plan_DataExodus.docx"
    doc.save(str(out))
    print(f"[done] {out.name}")


if __name__ == "__main__":
    build()
