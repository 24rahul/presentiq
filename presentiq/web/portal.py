"""Student portal for PresentIQ pilot study.

Provides clerkship selection, case dashboards, and account setup.
"""

from urllib.parse import urlsplit

import streamlit as st
import yaml

from presentiq.paths import CONFIG_DIR
from presentiq.web.state import reset_submission

# Configuration

_CONFIG_PATH = CONFIG_DIR / "clerkships.yaml"


def load_clerkship_config():
    """Load and return the clerkship configuration dict."""
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


# Navigation helpers


def _go_to(page, **extra_state):
    """Navigate from a widget callback before the next page is rendered."""
    st.session_state.page = page
    for k, v in extra_state.items():
        st.session_state[k] = v


def _reset_presentiq_state():
    """Clear PresentIQ session state for a fresh case."""
    reset_submission(st.session_state)


def _start_case(case, index):
    _reset_presentiq_state()
    _go_to("presentiq", active_case=case, active_case_index=index)


def _configured_link(label, url, key):
    """Do not send students to unfinished example URLs."""
    parsed = urlsplit(url or "")
    if parsed.scheme in ("http", "https") and parsed.netloc and "placeholder" not in url.lower():
        st.link_button(label, url, use_container_width=True)
    else:
        st.button(label, key=key, disabled=True, use_container_width=True)
        st.caption("Link not yet available. Please contact the study team.")


# Page: Clerkship Selection


def _render_teachable_signup(config):
    """Show account creation instructions alongside the student workflow."""
    teachable = config.get("teachable", {})
    signup_url = teachable.get("signup_url")
    signup_code = teachable.get("signup_code")
    if not signup_url or not signup_code:
        return

    with st.expander("Create your Teachable account", expanded=True):
        st.markdown("Set up your account before reviewing your assigned cases.")
        st.markdown(
            "1. Select **Create Teachable Account** below to open the registration page.\n"
            "2. Choose a **Username** and **Password**, then enter the same password "
            "in **Password confirmation**.\n"
            f"3. Enter `{signup_code}` in the **Sign-Up Code** field exactly as shown.\n"
            "4. Select **Sign Up** to create your account.\n"
            "5. Return to PresentIQ, select your clerkship if needed, and choose "
            "**Review on Teachable** for your assigned case. After reviewing the "
            "case, return here and select **Record Presentation**."
        )
        st.link_button("Create Teachable Account", signup_url, use_container_width=True)
        st.caption(
            "Already have an account? Open your assigned case and sign in "
            "with your existing username and password."
        )


def render_clerkship_selection(config):
    """Render the clerkship selection / landing page."""
    st.title("PresentIQ")
    st.subheader("Medical Presentation Feedback System")
    st.caption(
        "Created by Rahul Gorijavolu and Emily Zhao at the Johns Hopkins University School of Medicine"
    )

    st.markdown("---")
    st.markdown("### Welcome to the PresentIQ Pilot Study")
    st.markdown("Select your clerkship to view your assigned cases and surveys.")

    clerkships = config.get("clerkships", {})
    options = list(clerkships.keys())
    labels = {k: v.get("display_name", k) for k, v in clerkships.items()}

    selected = st.selectbox(
        "Select Your Clerkship",
        options,
        format_func=lambda x: labels.get(x, x),
        index=None,
        placeholder="Choose your clerkship...",
    )

    if selected:
        st.button(
            "Continue",
            type="primary",
            use_container_width=True,
            on_click=_go_to,
            args=("dashboard",),
            kwargs={"selected_clerkship": selected, "clerkship_data": clerkships[selected]},
        )

    st.markdown("---")
    with st.expander("Advanced Mode (Researcher Access)"):
        st.caption("Use PresentIQ without the student portal — full configuration access.")
        st.button("Open Advanced Mode", on_click=_go_to, args=("advanced",))


# Page: Dashboard


def render_dashboard(config):
    """Render the student dashboard with surveys and case cards."""
    clerkship = st.session_state.get("clerkship_data", {})

    if not clerkship:
        _go_to("select_clerkship")
        st.rerun()
        return

    st.title("PresentIQ")
    st.subheader(f"{clerkship.get('display_name', '')} — Student Dashboard")

    if clerkship.get("resource_provider") == "scholarrx":
        st.info(
            "Neurology uses the ScholarRx Neurology Clinical Bricks Library. "
            "Choose at least one clinical brick for your presentation. "
            "The hosted ARGOS version includes an integrated reader for openly licensed bricks."
        )
        for material in clerkship.get("materials", []):
            _configured_link(material["title"], material["resource_url"], material["id"])
    else:
        _render_teachable_signup(config)

    # --- Surveys ---
    surveys = config.get("surveys", [])
    if surveys:
        st.markdown("### Surveys")
        for index, survey in enumerate(surveys):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{survey.get('title', 'Survey')}**")
            with col2:
                _configured_link("Open Survey", survey.get("url"), f"survey_link_{index}")
        st.markdown("---")

    # --- Cases ---
    st.markdown("### Your Cases")
    cases = clerkship.get("cases", [])

    for i, case in enumerate(cases):
        with st.container():
            st.markdown(f"#### {case.get('title', f'Case {i + 1}')}")
            col_info, col_teachable, col_record = st.columns([3, 1.5, 1.5])
            with col_info:
                service_label = case.get("service", "").replace("_", " ").title()
                fmt_label = case.get("presentation_format", "").replace("_", " ").title()
                st.caption(f"Service: {service_label} | Format: {fmt_label}")
            with col_teachable:
                _configured_link(
                    "Read on ScholarRx"
                    if clerkship.get("resource_provider") == "scholarrx"
                    else "Review on Teachable",
                    case.get("resource_url") or case.get("teachable_url"),
                    f"case_link_{i}",
                )
            with col_record:
                st.button(
                    "Record Presentation",
                    key=f"record_{i}",
                    use_container_width=True,
                    on_click=_start_case,
                    args=(case, i),
                )
            st.markdown("---")

    # --- Back / Logout ---
    st.button("Change Clerkship", on_click=_go_to, args=("select_clerkship",))


# Data packaging
