"""Generate a self-contained HTML report that mirrors the PresentIQ web UI."""

from datetime import datetime


def _esc(text):
    """Escape HTML entities."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate_html_report(feedback, transcript, clerkship_name, case, ai_provider, model):
    """Return a self-contained HTML string that renders like the PresentIQ web UI."""

    agent_results = feedback.get("_agent_results", {})
    score = feedback.get("overall_score", "N/A")
    fmt = feedback.get("presentation_format", case.get("presentation_format", "Standard"))
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # --- Build tab content sections ---

    overview_html = _build_overview(feedback)
    reasoning_html = _build_reasoning(agent_results)
    structure_html = _build_structure(agent_results)
    rewrites_html = _build_rewrites(agent_results)
    deliberation_html = _build_deliberation(feedback, agent_results)
    monologue_html = _build_monologue(agent_results)
    learning_html = _build_learning(feedback, agent_results)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PresentIQ Report — {_esc(case.get("title", ""))}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #2c3e50; line-height: 1.6; }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem; }}
  .header {{ text-align: center; margin-bottom: 2rem; }}
  .header h1 {{ font-size: 2rem; color: #2c3e50; }}
  .header .meta {{ color: #7f8c8d; font-size: 0.9rem; margin-top: 0.5rem; }}
  .score-banner {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 1rem; border-radius: 8px; text-align: center; font-size: 1.2rem; font-weight: bold; margin: 1rem 0 2rem; }}
  .tabs {{ display: flex; flex-wrap: wrap; gap: 6px; background: rgba(52,152,219,0.1); border-radius: 8px; padding: 4px; margin-bottom: 1.5rem; }}
  .tab-btn {{ padding: 8px 16px; border: none; border-radius: 6px; background: transparent; cursor: pointer; font-weight: 500; color: #2c3e50; font-size: 0.85rem; }}
  .tab-btn.active {{ background: #3498db; color: white; }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  h2 {{ font-size: 1.3rem; color: #2c3e50; margin: 1.5rem 0 0.5rem; border-bottom: 2px solid #3498db; padding-bottom: 0.3rem; }}
  h3 {{ font-size: 1.1rem; color: #34495e; margin: 1rem 0 0.4rem; }}
  p, li {{ margin-bottom: 0.5rem; }}
  ul {{ padding-left: 1.5rem; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  @media (max-width: 640px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
  .card {{ background: white; border-radius: 8px; padding: 1.2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .info-box {{ background: #eaf4fd; border-left: 4px solid #3498db; padding: 0.8rem 1rem; border-radius: 0 6px 6px 0; margin: 0.5rem 0; }}
  .warn-box {{ background: #fef5e7; border-left: 4px solid #f39c12; padding: 0.8rem 1rem; border-radius: 0 6px 6px 0; margin: 0.5rem 0; }}
  .success-box {{ background: #eafaf1; border-left: 4px solid #27ae60; padding: 0.8rem 1rem; border-radius: 0 6px 6px 0; margin: 0.5rem 0; }}
  .thought-bubble {{ background: #f0f7ff; border-left: 4px solid #3498db; padding: 0.8rem 1rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0; }}
  .thought-type-questioning {{ border-left-color: #e67e22; }}
  .thought-type-concerned {{ border-left-color: #e74c3c; }}
  .thought-type-impressed {{ border-left-color: #27ae60; }}
  .thought-type-satisfied {{ border-left-color: #27ae60; }}
  .thought-type-confused {{ border-left-color: #e74c3c; }}
  .thought-type-expecting {{ border-left-color: #f39c12; }}
  .thought-type-noting {{ border-left-color: #95a5a6; }}
  .transcript-section {{ background: white; border-radius: 8px; padding: 1.5rem; margin-top: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .transcript-section pre {{ white-space: pre-wrap; word-wrap: break-word; font-family: inherit; font-size: 0.95rem; line-height: 1.7; }}
  .footer {{ text-align: center; color: #95a5a6; font-size: 0.8rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #ecf0f1; }}
  hr {{ border: none; border-top: 1px solid #ecf0f1; margin: 1rem 0; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>PresentIQ Feedback Report</h1>
    <div class="meta">
      {_esc(clerkship_name)} &middot; {_esc(case.get("title", ""))} &middot; {_esc(timestamp)}<br>
      AI Provider: {_esc(ai_provider)} &middot; Model: {_esc(model)}
    </div>
  </div>

  <div class="score-banner">
    Performance Score: {_esc(str(score))}/10 &nbsp;|&nbsp; Format: {_esc(fmt)}
  </div>

  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab(event, 'overview')">Overview</button>
    <button class="tab-btn" onclick="switchTab(event, 'reasoning')">Clinical Reasoning</button>
    <button class="tab-btn" onclick="switchTab(event, 'structure')">Structure &amp; Efficiency</button>
    <button class="tab-btn" onclick="switchTab(event, 'rewrites')">Before / After</button>
    <button class="tab-btn" onclick="switchTab(event, 'deliberation')">Deliberation</button>
    <button class="tab-btn" onclick="switchTab(event, 'monologue')">Attending Inner Monologue</button>
    <button class="tab-btn" onclick="switchTab(event, 'learning')">Teaching Points</button>
  </div>

  <div id="overview" class="tab-content active">{overview_html}</div>
  <div id="reasoning" class="tab-content">{reasoning_html}</div>
  <div id="structure" class="tab-content">{structure_html}</div>
  <div id="rewrites" class="tab-content">{rewrites_html}</div>
  <div id="deliberation" class="tab-content">{deliberation_html}</div>
  <div id="monologue" class="tab-content">{monologue_html}</div>
  <div id="learning" class="tab-content">{learning_html}</div>

  <div class="transcript-section">
    <h2>Transcript</h2>
    <pre>{_esc(transcript)}</pre>
  </div>

  <div class="footer">
    Generated by PresentIQ &mdash; Created by Rahul Gorijavolu and Emily Zhao at the Johns Hopkins University School of Medicine
  </div>
</div>

<script>
function switchTab(e, tabId) {{
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  e.target.classList.add('active');
}}
</script>
</body>
</html>"""


def _build_overview(feedback):
    parts = []
    parts.append(
        f"<h2>Overall Assessment</h2><p>{_esc(feedback.get('overall_assessment', 'No assessment provided.'))}</p>"
    )

    parts.append('<div class="two-col">')
    # Left column
    parts.append("<div>")
    parts.append(
        f"<h3>Clinical Content</h3><p>{_esc(feedback.get('clinical_content', 'No feedback provided.'))}</p>"
    )
    if feedback.get("strengths"):
        parts.append("<h3>Strengths</h3><ul>")
        for s in feedback["strengths"]:
            parts.append(f"<li>{_esc(s)}</li>")
        parts.append("</ul>")
    parts.append("</div>")
    # Right column
    parts.append("<div>")
    parts.append(
        f"<h3>Clinical Reasoning</h3><p>{_esc(feedback.get('clinical_reasoning', 'No feedback provided.'))}</p>"
    )
    if feedback.get("areas_for_improvement"):
        parts.append("<h3>Areas for Improvement</h3><ul>")
        for a in feedback["areas_for_improvement"]:
            parts.append(f"<li>{_esc(a)}</li>")
        parts.append("</ul>")
    parts.append("</div>")
    parts.append("</div>")

    if feedback.get("plan_coherence_summary"):
        parts.append(f"<h3>Plan Coherence</h3><p>{_esc(feedback['plan_coherence_summary'])}</p>")
    if feedback.get("semantic_density_summary"):
        parts.append(
            f"<h3>Information Efficiency</h3><p>{_esc(feedback['semantic_density_summary'])}</p>"
        )
    parts.append(
        f"<h3>Communication &amp; Professionalism</h3><p>{_esc(feedback.get('communication_professionalism', 'No feedback provided.'))}</p>"
    )
    if feedback.get("service_specific_feedback"):
        parts.append(
            f"<h3>Service-Specific Feedback</h3><p>{_esc(feedback['service_specific_feedback'])}</p>"
        )
    return "\n".join(parts)


def _build_reasoning(agent_results):
    reasoning = agent_results.get("clinical_reasoning", {})
    if not reasoning:
        return '<div class="info-box">Clinical reasoning data not available.</div>'
    parts = []
    parts.append(
        f"<h2>Differential Diagnosis</h2><p>{_esc(reasoning.get('differential_assessment', 'Not available.'))}</p>"
    )
    parts.append(
        f"<h2>Summary Statement Quality</h2><p>{_esc(reasoning.get('summary_statement_quality', 'Not available.'))}</p>"
    )
    parts.append(
        f"<h2>Data Selectivity</h2><p>{_esc(reasoning.get('data_selectivity', 'Not available.'))}</p>"
    )
    parts.append(
        f'<h2>Plan Coherence</h2><div class="info-box">{_esc(reasoning.get("plan_coherence", "Not available."))}</div>'
    )
    parts.append('<div class="two-col"><div><h3>Reasoning Strengths</h3><ul>')
    for s in reasoning.get("reasoning_strengths", []):
        parts.append(f"<li>{_esc(s)}</li>")
    parts.append("</ul></div><div><h3>Reasoning Gaps</h3><ul>")
    for g in reasoning.get("reasoning_gaps", []):
        parts.append(f"<li>{_esc(g)}</li>")
    parts.append("</ul></div></div>")
    return "\n".join(parts)


def _build_structure(agent_results):
    structure = agent_results.get("structure_delivery", {})
    if not structure:
        return '<div class="info-box">Structure data not available.</div>'
    parts = []
    parts.append(
        f"<h2>Format Conformance</h2><p>{_esc(structure.get('format_conformance', 'Not available.'))}</p>"
    )
    parts.append('<div class="two-col"><div><h3>Sections Present</h3><ul>')
    for s in structure.get("sections_present", []):
        parts.append(f"<li>[+] {_esc(s)}</li>")
    parts.append("</ul></div><div><h3>Sections Missing</h3><ul>")
    for s in structure.get("sections_missing", []):
        parts.append(f"<li>[-] {_esc(s)}</li>")
    parts.append("</ul></div></div>")
    parts.append(
        f"<h2>Organization &amp; Flow</h2><p>{_esc(structure.get('organization_flow', 'Not available.'))}</p>"
    )
    sd = structure.get("semantic_density", {})
    if sd:
        parts.append(
            f"<h2>Semantic Density / Information Efficiency</h2><p>{_esc(sd.get('analysis', 'Not available.'))}</p>"
        )
        parts.append(
            f"<p><strong>Efficiency Rating:</strong> {_esc(sd.get('efficiency_rating', 'unknown'))}</p>"
        )
        parts.append('<div class="two-col"><div>')
        if sd.get("over_represented"):
            parts.append("<p><strong>Over-represented (too much time):</strong></p><ul>")
            for item in sd["over_represented"]:
                parts.append(f"<li>{_esc(item)}</li>")
            parts.append("</ul>")
        parts.append("</div><div>")
        if sd.get("under_represented"):
            parts.append("<p><strong>Under-represented (too little time):</strong></p><ul>")
            for item in sd["under_represented"]:
                parts.append(f"<li>{_esc(item)}</li>")
            parts.append("</ul>")
        parts.append("</div></div>")
    return "\n".join(parts)


def _build_rewrites(agent_results):
    contrastive = agent_results.get("contrastive_feedback", {})
    rewrites = contrastive.get("rewrites", [])
    if not rewrites:
        return (
            '<div class="info-box">No contrastive rewrites were generated for this analysis.</div>'
        )
    parts = []
    parts.append("<h2>How Key Sections Could Be Improved</h2>")
    parts.append("<p><em>Concrete before/after examples for the highest-impact areas.</em></p>")
    for rw in rewrites:
        parts.append(f"<h3>{_esc(rw.get('area', 'Improvement'))}</h3>")
        parts.append('<div class="two-col">')
        parts.append(
            f'<div><p><em>Original:</em></p><div class="warn-box">{_esc(rw.get("original", ""))}</div></div>'
        )
        parts.append(
            f'<div><p><em>Improved:</em></p><div class="success-box">{_esc(rw.get("improved", ""))}</div></div>'
        )
        parts.append("</div>")
        if rw.get("uses_illustrative_data"):
            parts.append(
                "<p><em>Note: Bracketed values [e.g., ...] are illustrative — substitute the patient's actual data.</em></p>"
            )
        parts.append(f"<p><em>{_esc(rw.get('why_better', ''))}</em></p><hr>")
    if contrastive.get("note"):
        parts.append(f'<div class="info-box">{_esc(contrastive["note"])}</div>')
    return "\n".join(parts)


def _build_deliberation(feedback, agent_results):
    debate = agent_results.get("debate", {})
    contested = debate.get("contested_points", [])
    parts = []
    if contested:
        parts.append("<h2>Generous vs. Strict Evaluator Deliberation</h2>")
        parts.append(
            "<p><em>Two evaluator perspectives debated the assessment to produce more calibrated feedback.</em></p>"
        )
        for cp in contested:
            parts.append(
                f"<h3>{_esc(cp.get('dimension', 'General'))} — Adjustment: <code>{_esc(cp.get('adjustment', 'keep'))}</code></h3>"
            )
            parts.append('<div class="two-col">')
            parts.append(
                f'<div><p><em>Generous Evaluator:</em></p><div class="info-box">{_esc(cp.get("generous_view", ""))}</div></div>'
            )
            parts.append(
                f'<div><p><em>Strict Evaluator:</em></p><div class="warn-box">{_esc(cp.get("strict_view", ""))}</div></div>'
            )
            parts.append("</div>")
            parts.append(
                f"<p><strong>Resolution:</strong> {_esc(cp.get('resolution', ''))}</p><hr>"
            )
        parts.append('<div class="two-col"><div>')
        if debate.get("consensus_strengths"):
            parts.append("<h3>Both Agree: Strengths</h3><ul>")
            for s in debate["consensus_strengths"]:
                parts.append(f"<li>{_esc(s)}</li>")
            parts.append("</ul>")
        parts.append("</div><div>")
        if debate.get("consensus_weaknesses"):
            parts.append("<h3>Both Agree: Needs Work</h3><ul>")
            for w in debate["consensus_weaknesses"]:
                parts.append(f"<li>{_esc(w)}</li>")
            parts.append("</ul>")
        parts.append("</div></div>")
        if debate.get("overall_calibration"):
            parts.append(
                f"<h3>Calibration Assessment</h3><p>{_esc(debate['overall_calibration'])}</p>"
            )
    else:
        parts.append(
            '<div class="info-box">Deliberation results not available for this analysis.</div>'
        )

    critic = agent_results.get("synthesis_critic", {})
    if critic and critic.get("issues_found"):
        parts.append("<hr><h2>Synthesis Quality Review</h2>")
        for issue in critic["issues_found"]:
            parts.append(
                f"<h3>{_esc(issue.get('type', 'issue').replace('_', ' ').title())} — {_esc(issue.get('location', ''))}</h3>"
            )
            parts.append(f"<p>{_esc(issue.get('description', ''))}</p>")
            parts.append(f"<p><em>Fix: {_esc(issue.get('suggested_fix', ''))}</em></p>")
        if feedback.get("_revised"):
            parts.append(
                '<div class="success-box">The synthesis was automatically revised to address these issues.</div>'
            )
    return "\n".join(parts)


def _build_monologue(agent_results):
    anticipatory = agent_results.get("anticipatory_reasoning", {})
    monologue = anticipatory.get("inner_monologue", [])
    if not monologue:
        return '<div class="info-box">Attending Inner Monologue was not enabled for this analysis.</div>'
    parts = []
    parts.append("<h2>What an Attending Would Be Thinking</h2>")
    parts.append(
        "<p><em>This experimental feature shows the inner monologue of an experienced attending as they listen to your presentation.</em></p>"
    )
    for entry in monologue:
        thought_type = entry.get("thought_type", "noting")
        parts.append(f'<div class="thought-bubble thought-type-{_esc(thought_type)}">')
        parts.append(f"<strong>[{_esc(thought_type.upper())}]</strong><br>")
        parts.append(f'<em>Hearing:</em> "{_esc(entry.get("transcript_segment", ""))}"<br><br>')
        parts.append(
            f"<strong>Attending thinks:</strong> {_esc(entry.get('attending_thought', ''))}"
        )
        parts.append("</div>")

    if anticipatory.get("unanswered_questions"):
        parts.append("<h3>Questions Left Unanswered</h3><ul>")
        for q in anticipatory["unanswered_questions"]:
            parts.append(f"<li>{_esc(q)}</li>")
        parts.append("</ul>")

    parts.append('<div class="two-col"><div>')
    if anticipatory.get("anticipatory_strengths"):
        parts.append("<h3>Anticipated Well</h3><ul>")
        for s in anticipatory["anticipatory_strengths"]:
            parts.append(f"<li>{_esc(s)}</li>")
        parts.append("</ul>")
    parts.append("</div><div>")
    if anticipatory.get("missed_anticipations"):
        parts.append("<h3>Could Have Anticipated</h3><ul>")
        for m in anticipatory["missed_anticipations"]:
            parts.append(f"<li>{_esc(m)}</li>")
        parts.append("</ul>")
    parts.append("</div></div>")

    if anticipatory.get("overall_impression"):
        parts.append(
            f"<h3>Overall Listener Impression</h3><p>{_esc(anticipatory['overall_impression'])}</p>"
        )
    return "\n".join(parts)


def _build_learning(feedback, agent_results):
    literature = agent_results.get("literature_learning", {})
    parts = []
    if literature.get("case_learning_summary"):
        parts.append(
            f"<h2>Case Learning Summary</h2><p>{_esc(literature['case_learning_summary'])}</p>"
        )
    teaching_points = literature.get("teaching_points", [])
    if teaching_points:
        parts.append("<h2>Teaching Points</h2>")
        for tp in teaching_points:
            if isinstance(tp, dict):
                parts.append(f"<h3>{_esc(tp.get('topic', 'Teaching Point'))}</h3>")
                parts.append(f"<p>{_esc(tp.get('point', ''))}</p>")
                if tp.get("relevance"):
                    parts.append(f"<p><em>Relevance: {_esc(tp['relevance'])}</em></p>")
                parts.append("<hr>")
            else:
                parts.append(f"<p>- {_esc(tp)}</p>")
    reading = literature.get("suggested_reading", [])
    if reading:
        parts.append("<h2>Suggested Reading</h2><ul>")
        for r in reading:
            parts.append(f"<li>{_esc(r)}</li>")
        parts.append("</ul>")
    synth_tp = feedback.get("teaching_points", [])
    if synth_tp and synth_tp != teaching_points:
        parts.append("<h2>Key Takeaways</h2><ul>")
        for tp in synth_tp:
            parts.append(f"<li>{_esc(tp)}</li>")
        parts.append("</ul>")
    if not parts:
        return '<div class="info-box">Teaching points not available for this analysis.</div>'
    return "\n".join(parts)
