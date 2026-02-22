# Architecture : Streamlit (UI + Memory) -> FastAPI (Validation + Conversion) -> LangGraph ReAct Agent(Handles reasoning, Calls tools if needed) 
# -> Groq LLM + Tavily Search (Generates final answer, Uses Tavily if search enabled) -> Response
# Complete Flow in Real Time: User types message, Streamlit stores in session, Payload sent to FastAPI, FastAPI validates request,Messages converted to LangChain format,
# ReAct agent invoked,Groq LLM generates response, Response returned, Streamlit displays answer, Memory updated

import streamlit as st
import requests #Used to send HTTP requests to backend

from app.config.settings import settings
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

# Page Config
# Browser tab title
st.set_page_config(page_title="Multi AI Agent", layout="centered")
# Displays main page heading
st.title("🤖 Multi AI Agent using Groq + Tavily Search")

# Initialize Session State
# Streamlit reruns script on every interaction. Without session_state: Chat would reset every time. This creates persistent memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar Controls # Creates sidebar section. Separates configuration from chat UI.
st.sidebar.header("⚙️ Agent Configuration")

# Allows user to define agent behavior. This is passed to backend and injected into agent. eg : You are a strict coding assistant.
system_prompt = st.sidebar.text_area(
    "Define your AI Agent:",
    height=100,
    placeholder="You are a helpful AI assistant..."
)

#Dropdown list of allowed models. Pulled from config. Prevents invalid model names.
selected_model = st.sidebar.selectbox(
    "Select your AI model:",
    settings.ALLOWED_MODEL_NAMES
)

# Boolean Web toggle.If True: Backend enables Tavily search tool.If False:Pure LLM mode.
allow_web_search = st.sidebar.checkbox("Allow web search")

#Resets conversation memory.
if st.sidebar.button("Clear Chat"):
    st.session_state.chat_history = []
    st.success("Chat cleared!")

# Display Chat History: Loops over stored messages. Each message has a role (user/assistant) and content. Displays in correct format.
#"system" message/role type  is: Used by backend, Not stored in frontend chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]): #Displays: User bubble if role == "user",Assistant bubble if role == "assistant", Streamlit automatically styles them differently.
        st.markdown(message["content"]) #Renders message content as markdown. Allows for better formatting in AI responses.

# User Input,Modern chat-style input box. When user submits, it triggers the flow to send the message to backend and get AI response.
user_query = st.chat_input("Ask your query to agent...")

#Backend endpoint. This is where our FastAPI server is running. The UI will send a POST request to this endpoint with the user query and configuration, and expect a response back.
API_URL = settings.FAST_API_URL

# On User Message
if user_query:

    # Append user message to chat history session, Frontend memory must match backend schema.
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_query
    })

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_query)

    # Prepare payload in correct backend format. This must match FastAPI schema.
    # Backend expects: model_name, system_prompt, messages (list of dicts with role and content), allow_search boolean
    payload = {
        "model_name": selected_model,
        "system_prompt": system_prompt,
        "messages": st.session_state.chat_history,
        "allow_search": allow_web_search
    }

    try:
        logger.info("Sending request to backend")

        #This connects our UI → FastAPI server, Sends POST request.timeout=60 prevents hanging forever.
        response = requests.post(API_URL, json=payload, timeout=60)

        #Successful backend execution.
        if response.status_code == 200:
            # Gets AI answer from JSON. Extract response.
            agent_response = response.json().get("response", "")

            # Append assistant message to session.Adds AI reply to memory.Now conversation continues correctly.
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": agent_response
            })

            # Display assistant message,Shows AI response bubble.
            with st.chat_message("assistant"):
                st.markdown(agent_response)

            logger.info("Successfully received response from backend")

        else:
            logger.error("Backend returned error")
            #Shows error message returned from FastAPI.
            st.error(response.json().get("detail", "Error from backend"))

    #Catches:Network failure,Server not running,Timeout,Unexpected error
    except Exception as e:
        logger.error(f"Error communicating with backend: {str(e)}")
        #Displays custom error to user.
        st.error(str(CustomException("Failed to communicate with backend")))
