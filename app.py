import streamlit as st
from openai import OpenAI
import time

# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(page_title="HTC Fundraising App", page_icon="📝")

# --- PASSWORD PROTECTION START ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    # Return True if the pass was verified earlier in the session
    if "password_correct" in st.session_state:
        if st.session_state["password_correct"]:
            return True

    # Show input for password
    st.title("🔒 Client Login")
    st.text_input(
        "Please enter the password to access the Fundraising Assistant:", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")

    return False

if not check_password():
    st.stop()  # Stop execution if password is wrong
# --- PASSWORD PROTECTION END ---


# 2. Main App Logic (Only runs if password is correct)
st.title("HTC Fundraising Assistant")

# Load secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    assistant_id = st.secrets["ASSISTANT_ID"]
except FileNotFoundError:
    st.error("Secrets not found. Please set OPENAI_API_KEY and ASSISTANT_ID in Streamlit settings.")
    st.stop()

client = OpenAI(api_key=api_key)

# 3. Session State Management
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Handle User Input
if prompt := st.chat_input("How can I help with the fundraising letter?"):
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Send to OpenAI
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    # Run the Assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id
    )

    # Wait for completion (Polling)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            while run.status != "completed":
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
            
            # Retrieve the latest message from the assistant
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            assistant_msg = messages.data[0].content[0].text.value
            st.markdown(assistant_msg)
    
    # Save assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
