# 03 — Strategic SWOT & Competitor Matrix

> ⚠️ **DRAFT — BASED ON MISSING DATA**
> Written from `README.md` only. We do not know what data, tools or criteria Traficom will share, or what other teams will build. Competitor entries are **predictions** `[HYPOTHESIS]`, not observations. Re-check after the Friday briefing and the Saturday Q&A.

---

## 1. SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **Strengths**<br>• Narrow, specific product (Filing Radar) instead of a generic assistant.<br>• Data adapter lets us demo on synthetic data and switch to real data with one file edit.<br>• Every flag is cited → directly answers "explainable AI" and "transparent" `[README]`.<br>• Human approve/dismiss loop answers "experts firmly in control" `[README]`. | **Weaknesses**<br>• No spectrum-regulation expert on the team `[HYPOTHESIS — team unknown]`.<br>• Real ITU data formats (SRS `.mdb`, GXT) may be slow to parse `[GAP - ASK PARTNER]`.<br>• Interference maths is easy to get wrong; we must label it "indicative".<br>• Team size and roles not yet known. |
| **External** | **Opportunities**<br>• **The narrow README is our biggest advantage.** Most teams will turn a vague brief into a generic chatbot. A concrete, operational tool that matches the README's four verbs (discover, understand, connect, identify) will stand out.<br>• Partner Q&A on Saturday lets us validate early while others are still guessing.<br>• Public sources (Radio Regulations, Finnish frequency plan) exist even with zero partner data `[HYPOTHESIS]`. | **Threats**<br>• Partner gives only PDFs or nothing at 19:30.<br>• NDA forbids cloud LLMs → slower local models.<br>• Evaluators value something we haven't guessed (e.g. a different user, or policy analysis instead of technical screening).<br>• A team with real spectrum expertise. |

---

## 2. Competitor Matrix: Us vs 3 "Lazy README Interpretations" `[HYPOTHESIS]`

| Dimension | **Us: Filing Radar** | A: "Chat with the Radio Regulations" (RAG chatbot) | B: Filing PDF Summariser | C: Pretty 3D Satellite Visualiser |
|---|---|---|---|---|
| Solves "discover relevant filings" | ✅ Ranks a whole circular | ❌ User must know what to ask | ⚠️ One file at a time | ❌ |
| "Understand implications" for **Finland** | ✅ Overlap vs Finnish assets | ⚠️ Generic answers | ⚠️ Generic summary | ⚠️ Visual only |
| "Connect evidence across sources" | ✅ Cited filing + rule + asset | ⚠️ Citations to rules only | ❌ | ❌ |
| "Identify situations worth investigating" | ✅ Score + reasons | ❌ | ❌ | ❌ |
| Human in control | ✅ Approve / dismiss / audit log | ⚠️ Implicit | ⚠️ Implicit | n/a |
| 15-second "wow" | ✅ Footprint lights up over Finland, click → source | ⚠️ Looks like every other chatbot | ❌ Text wall | ✅ Looks great, no substance |
| Works with zero partner data | ✅ Synthetic Branch B | ✅ | ⚠️ Needs PDFs | ✅ |

**Where they beat us:** C will look prettier. A will be faster to build. Our answer: borrow C's visual hook (map) and keep A's citations, but attach both to a real decision.

---

## 3. Strategic Verdict

**Unfair advantage (1 sentence):**
We are the only team likely to turn "a new transmission planned far away" into a ranked, cited, Finland-specific shortlist that a Traficom expert can approve in one click.

**30-second elevator pitch:**
"Every few weeks a new international circular lists many new satellite filings, and Traficom's experts must find the few that could interfere with systems in Finland before the comment deadline. Today that means reading filings by hand and cross-checking several sources. Filing Radar does the first pass: it extracts the technical parameters, checks frequencies and coverage against Finland's protected systems, and ranks what's worth investigating. Every flag links to its exact source, and the expert makes every decision. Same experts, same control, minutes instead of days for the first pass."

> Figures like "every few weeks" and "minutes instead of days" are `[HYPOTHESIS]`. Replace them with partner numbers before the video.
