# frontend.py
import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000/graph"  # change if your backend host/port differ

st.set_page_config(page_title="Travel Planner", page_icon="✈️")
st.title("✈️ Smart Travel Planner")

# --- Session state defaults ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "messages" not in st.session_state:
    # list of tuples: ("user"|"assistant", text)
    st.session_state.messages = []
if "awaiting_feedback" not in st.session_state:
    st.session_state.awaiting_feedback = False
if "show_feedback_box" not in st.session_state:
    st.session_state.show_feedback_box = False
if "last_assistant" not in st.session_state:
    st.session_state.last_assistant = None  # store last assistant text to avoid duplicates

# Helper: append message once
def append_message(role: str, text: str):
    # avoid adding duplicates of last assistant message
    if role == "assistant":
        if text is None:
            return
        if st.session_state.last_assistant == text:
            return
        st.session_state.last_assistant = text
    st.session_state.messages.append((role, text))

# Helper: call backend start/resume and return parsed json or raise
def call_backend_start(human_prompt: str):
    res = requests.post(f"{API_BASE}/start", json={"human_prompt": human_prompt})
    res.raise_for_status()
    return res.json()

def call_backend_resume(thread_id: str, review_action: str, human_feedback: str | None = None):
    payload = {
        "thread_id": thread_id,
        "review_action": review_action,
        "human_feedback": human_feedback,
    }
    res = requests.post(f"{API_BASE}/resume", json=payload)
    res.raise_for_status()
    return res.json()

# Render chat history
def render_chat():
    for role, text in st.session_state.messages:
        with st.chat_message(role):
            st.markdown(text)

render_chat()

# Input area: disable whenever approval is pending
user_input = st.chat_input(
    "Type your message here...",
    disabled=st.session_state.awaiting_feedback,
)

# Handle user input (new message)
if user_input:
    append_message("user", user_input)
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                if st.session_state.thread_id is None:
                    data = call_backend_start(user_input)
                else:
                    # Free-typed messages count as feedback unless user clicks Approve
                    data = call_backend_resume(
                        st.session_state.thread_id, "feedback", human_feedback=user_input
                    )
    except requests.RequestException as e:
        st.error(f"Could not reach backend: {e}")
    else:
        st.session_state.thread_id = data.get("thread_id", st.session_state.thread_id)
        assistant_text = data.get("assistant_response", "")
        append_message("assistant", assistant_text)
        st.session_state.awaiting_feedback = data.get("run_status") == "awaiting_feedback"
        st.session_state.show_feedback_box = False
    st.rerun()

# Approval buttons appear only when backend is awaiting approval
if st.session_state.awaiting_feedback:
    st.markdown("---")
    st.write("### The assistant is waiting for your response")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✅ Approve", key="approve_btn"):
            try:
                with st.chat_message("assistant"):
                    with st.spinner("Generating your plan…"):
                        data = call_backend_resume(st.session_state.thread_id, "approved", None)
            except requests.RequestException as e:
                st.error(f"Could not reach backend: {e}")
            else:
                append_message("assistant", data.get("assistant_response", ""))
                st.session_state.awaiting_feedback = data.get("run_status") == "awaiting_feedback"
                if data.get("run_status") == "finished":
                    st.success("✅ Trip planning completed! You can continue chatting to make changes or ask follow-ups.")
            st.rerun()

    with col2:
        if st.button("✏️ Give Feedback", key="feedback_btn"):
            st.session_state.show_feedback_box = True
            st.rerun()

# Feedback form (separate block, not inside the button handler)
if st.session_state.show_feedback_box:
    st.markdown("---")
    st.write("Please enter your correction(s) or feedback below:")

    with st.form(key="feedback_form", clear_on_submit=False):
        feedback_text = st.text_area("Your feedback (e.g. change destination to Goa):", height=120)
        submitted = st.form_submit_button("Send Feedback")

    if submitted:
        if not feedback_text.strip():
            st.warning("Please type something for feedback.")
        else:
            append_message("user", f"Feedback: {feedback_text}")
            try:
                with st.chat_message("assistant"):
                    with st.spinner("Updating your plan…"):
                        data = call_backend_resume(st.session_state.thread_id, "feedback", feedback_text)
            except requests.RequestException as e:
                st.error(f"Could not reach backend: {e}")
            else:
                append_message("assistant", data.get("assistant_response", ""))
                st.session_state.awaiting_feedback = data.get("run_status") == "awaiting_feedback"
                st.session_state.show_feedback_box = False
                if data.get("run_status") == "finished":
                    st.success("✅ Trip planning completed! You can continue chatting to make changes or ask follow-ups.")
        st.rerun()
