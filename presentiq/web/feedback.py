"""Render validated feedback in the Streamlit interface."""

from html import escape

import streamlit as st


def display_multi_agent_feedback(feedback):
    agent_results = feedback.get("_agent_results", {})

    (
        tab_overview,
        tab_reasoning,
        tab_structure,
        tab_rewrites,
        tab_deliberation,
        tab_monologue,
        tab_learning,
    ) = st.tabs(
        [
            "Overview",
            "Clinical Reasoning",
            "Structure & Efficiency",
            "Before / After",
            "Deliberation",
            "Attending Inner Monologue",
            "Teaching Points",
        ]
    )

    with tab_overview:
        st.subheader("Overall Assessment")
        st.write(feedback.get("overall_assessment", "No assessment provided."))

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Clinical Content")
            st.write(feedback.get("clinical_content", "No feedback provided."))

            if feedback.get("strengths"):
                st.subheader("Strengths")
                for strength in feedback["strengths"]:
                    st.write(f"- {strength}")

        with col2:
            st.subheader("Clinical Reasoning")
            st.write(feedback.get("clinical_reasoning", "No feedback provided."))

            if feedback.get("areas_for_improvement"):
                st.subheader("Areas for Improvement")
                for area in feedback["areas_for_improvement"]:
                    st.write(f"- {area}")

        if feedback.get("plan_coherence_summary"):
            st.subheader("Plan Coherence")
            st.write(feedback["plan_coherence_summary"])

        if feedback.get("semantic_density_summary"):
            st.subheader("Information Efficiency")
            st.write(feedback["semantic_density_summary"])

        st.subheader("Communication & Professionalism")
        st.write(feedback.get("communication_professionalism", "No feedback provided."))

        if feedback.get("service_specific_feedback"):
            st.subheader("Service-Specific Feedback")
            st.write(feedback["service_specific_feedback"])

    with tab_reasoning:
        reasoning = agent_results.get("clinical_reasoning", {})
        if reasoning:
            st.subheader("Differential Diagnosis")
            st.write(reasoning.get("differential_assessment", "Not available."))

            st.subheader("Summary Statement Quality")
            st.write(reasoning.get("summary_statement_quality", "Not available."))

            st.subheader("Data Selectivity")
            st.write(reasoning.get("data_selectivity", "Not available."))

            st.subheader("Plan Coherence")
            st.info(reasoning.get("plan_coherence", "Not available."))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Reasoning Strengths")
                for s in reasoning.get("reasoning_strengths", []):
                    st.write(f"- {s}")
            with col2:
                st.subheader("Reasoning Gaps")
                for g in reasoning.get("reasoning_gaps", []):
                    st.write(f"- {g}")

    with tab_structure:
        structure = agent_results.get("structure_delivery", {})
        if structure:
            st.subheader("Format Conformance")
            st.write(structure.get("format_conformance", "Not available."))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Sections Present")
                for s in structure.get("sections_present", []):
                    st.write(f"[+] {s}")
            with col2:
                st.subheader("Sections Missing")
                for s in structure.get("sections_missing", []):
                    st.write(f"[-] {s}")

            st.subheader("Organization & Flow")
            st.write(structure.get("organization_flow", "Not available."))

            sd = structure.get("semantic_density", {})
            if sd:
                st.subheader("Semantic Density / Information Efficiency")
                st.write(sd.get("analysis", "Not available."))

                efficiency = sd.get("efficiency_rating", "unknown")
                st.write(f"**Efficiency Rating:** {efficiency}")

                col1, col2 = st.columns(2)
                with col1:
                    if sd.get("over_represented"):
                        st.write("**Over-represented (too much time):**")
                        for item in sd["over_represented"]:
                            st.write(f"- {item}")
                with col2:
                    if sd.get("under_represented"):
                        st.write("**Under-represented (too little time):**")
                        for item in sd["under_represented"]:
                            st.write(f"- {item}")

    with tab_rewrites:
        contrastive = agent_results.get("contrastive_feedback", {})
        rewrites = contrastive.get("rewrites", [])

        if rewrites:
            st.subheader("How Key Sections Could Be Improved")
            st.caption("Concrete before/after examples for the highest-impact areas.")

            for rw in rewrites:
                st.markdown(f"**{rw.get('area', 'Improvement')}**")

                col_before, col_after = st.columns(2)
                with col_before:
                    st.markdown("*Original:*")
                    st.warning(rw.get("original", ""))
                with col_after:
                    st.markdown("*Improved:*")
                    st.success(rw.get("improved", ""))

                if rw.get("uses_illustrative_data"):
                    st.caption(
                        "Note: Bracketed values [e.g., ...] are illustrative — substitute the patient's actual data."
                    )

                st.caption(rw.get("why_better", ""))
                st.markdown("---")

            if contrastive.get("note"):
                st.info(contrastive["note"])
        else:
            st.info("No contrastive rewrites were generated for this analysis.")

    with tab_deliberation:
        debate = agent_results.get("debate", {})
        contested = debate.get("contested_points", [])

        if contested:
            st.subheader("Generous vs. Strict Evaluator Deliberation")
            st.caption(
                "Two evaluator perspectives debated the assessment to produce more calibrated feedback."
            )

            for cp in contested:
                st.markdown(
                    f"**{cp.get('dimension', 'General')}** — Adjustment: `{cp.get('adjustment', 'keep')}`"
                )

                col_gen, col_strict = st.columns(2)
                with col_gen:
                    st.markdown("*Generous Evaluator:*")
                    st.info(cp.get("generous_view", ""))
                with col_strict:
                    st.markdown("*Strict Evaluator:*")
                    st.warning(cp.get("strict_view", ""))

                st.markdown(f"**Resolution:** {cp.get('resolution', '')}")
                st.markdown("---")

            col_s, col_w = st.columns(2)
            with col_s:
                consensus_strengths = debate.get("consensus_strengths", [])
                if consensus_strengths:
                    st.subheader("Both Agree: Strengths")
                    for s in consensus_strengths:
                        st.write(f"- {s}")
            with col_w:
                consensus_weaknesses = debate.get("consensus_weaknesses", [])
                if consensus_weaknesses:
                    st.subheader("Both Agree: Needs Work")
                    for w in consensus_weaknesses:
                        st.write(f"- {w}")

            if debate.get("overall_calibration"):
                st.subheader("Calibration Assessment")
                st.write(debate["overall_calibration"])
        else:
            st.info("Deliberation results not available for this analysis.")

        critic = agent_results.get("synthesis_critic", {})
        if critic and critic.get("issues_found"):
            st.markdown("---")
            st.subheader("Synthesis Quality Review")
            for issue in critic["issues_found"]:
                st.markdown(
                    f"**{issue.get('type', 'issue').replace('_', ' ').title()}** — {issue.get('location', '')}"
                )
                st.write(issue.get("description", ""))
                st.caption(f"Fix: {issue.get('suggested_fix', '')}")

            if feedback.get("_revised"):
                st.success("The synthesis was automatically revised to address these issues.")

    with tab_monologue:
        anticipatory = agent_results.get("anticipatory_reasoning", {})
        monologue = anticipatory.get("inner_monologue", [])

        if monologue:
            st.subheader("What an Attending Would Be Thinking")
            st.caption(
                "This experimental feature shows the inner monologue of an experienced attending as they listen to your presentation."
            )

            for entry in monologue:
                thought_type = entry.get("thought_type", "noting")

                st.markdown(
                    f"""<div class="thought-bubble thought-type-{escape(thought_type)}">
<strong>[{thought_type.upper()}]</strong><br>
<em>Hearing:</em> "{escape(entry.get("transcript_segment", ""))}"<br><br>
<strong>Attending thinks:</strong> {escape(entry.get("attending_thought", ""))}
</div>""",
                    unsafe_allow_html=True,
                )

            unanswered = anticipatory.get("unanswered_questions", [])
            if unanswered:
                st.subheader("Questions Left Unanswered")
                for q in unanswered:
                    st.write(f"- {q}")

            col1, col2 = st.columns(2)
            with col1:
                strengths = anticipatory.get("anticipatory_strengths", [])
                if strengths:
                    st.subheader("Anticipated Well")
                    for s in strengths:
                        st.write(f"- {s}")
            with col2:
                missed = anticipatory.get("missed_anticipations", [])
                if missed:
                    st.subheader("Could Have Anticipated")
                    for m in missed:
                        st.write(f"- {m}")

            if anticipatory.get("overall_impression"):
                st.subheader("Overall Listener Impression")
                st.write(anticipatory["overall_impression"])
        else:
            st.info(
                "Attending Inner Monologue was not enabled for this analysis. Enable it in the sidebar to see this feature."
            )

    with tab_learning:
        literature = agent_results.get("literature_learning", {})

        if literature.get("case_learning_summary"):
            st.subheader("Case Learning Summary")
            st.write(literature["case_learning_summary"])

        teaching_points = literature.get("teaching_points", [])
        if teaching_points:
            st.subheader("Teaching Points")
            for tp in teaching_points:
                if isinstance(tp, dict):
                    st.markdown(f"**{tp.get('topic', 'Teaching Point')}**")
                    st.write(tp.get("point", ""))
                    if tp.get("relevance"):
                        st.caption(f"Relevance: {tp['relevance']}")
                    st.markdown("---")
                else:
                    st.write(f"- {tp}")

        reading = literature.get("suggested_reading", [])
        if reading:
            st.subheader("Suggested Reading")
            for r in reading:
                st.write(f"- {r}")

        synth_tp = feedback.get("teaching_points", [])
        if synth_tp and synth_tp != teaching_points:
            st.subheader("Key Takeaways")
            for tp in synth_tp:
                st.write(f"- {tp}")


def display_legacy_feedback(feedback):
    st.subheader("Overall Assessment")
    st.write(feedback.get("overall_assessment", "No assessment provided."))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Clinical Content")
        st.write(feedback.get("clinical_content", "No feedback provided."))

        if feedback.get("strengths"):
            st.subheader("Strengths")
            for strength in feedback["strengths"]:
                st.write(f"- {strength}")

    with col2:
        st.subheader("Clinical Reasoning")
        st.write(feedback.get("clinical_reasoning", "No feedback provided."))

        if feedback.get("areas_for_improvement"):
            st.subheader("Areas for Improvement")
            for area in feedback["areas_for_improvement"]:
                st.write(f"- {area}")

    st.subheader("Presentation Structure")
    st.write(feedback.get("presentation_structure", "No feedback provided."))


# PresentIQ core flow — can be called with presets from portal or standalone
