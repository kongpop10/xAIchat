"""
Grok Chat - A Streamlit-based chat application for interacting with xAI's Grok models.
Features web search integration and Model Context Protocol (MCP) support.
"""
import streamlit as st
import uuid
import time

# Import from refactored modules
from icon import get_xai_favicon
from config import (
    load_settings, save_settings, load_mcp_settings, save_mcp_settings,
    create_default_mcp_settings, get_mcp_server_descriptions,
    DEFAULT_SETTINGS, MCP_SETTINGS_FILE
)
from models import fetch_xai_models
from conversation import load_conversations, save_conversation, create_new_conversation
from ui import (
    render_markdown_with_latex, display_with_copy_option, display_chat_message,
    show_thinking_indicator, setup_sidebar_model_settings, setup_sidebar_toggles,
    setup_mcp_settings_ui, display_conversation_history
)
from mcp import get_mcp_tool_descriptions
# Note: We're no longer using simulate_mcp_tool_usage
from ai import generate_response

# Load settings without Streamlit commands
settings = load_settings()

# Load MCP settings without Streamlit commands
mcp_settings = load_mcp_settings()
created_default_settings = False
if not mcp_settings or "mcpServers" not in mcp_settings or not mcp_settings["mcpServers"]:
    # Create default MCP settings if none exist
    mcp_settings = create_default_mcp_settings()
    created_default_settings = True

# Initialize the Streamlit app with the xAI favicon - MUST BE FIRST STREAMLIT COMMAND
xai_favicon = get_xai_favicon()
st.set_page_config(
    page_title="Grok Chat",
    page_icon=xai_favicon,  # xAI favicon as icon
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now we can show Streamlit messages after page config
if created_default_settings:
    st.success(f"Created default {MCP_SETTINGS_FILE} file. Please edit it to configure your MCP servers.")

# Initialize session state variables
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a highly intelligent AI assistant powered by the Grok model from xAI."}
    ]
if "conversations" not in st.session_state:
    st.session_state.conversations = load_conversations()
if "conversation_title" not in st.session_state:
    st.session_state.conversation_title = "New Conversation"

# Load settings from settings.json if present
if "reasoning_effort" not in st.session_state:
    st.session_state.reasoning_effort = settings.get("reasoning_effort", DEFAULT_SETTINGS["reasoning_effort"])
if "show_reasoning" not in st.session_state:
    st.session_state.show_reasoning = settings.get("show_reasoning", DEFAULT_SETTINGS["show_reasoning"])
if "model_name" not in st.session_state:
    st.session_state.model_name = settings.get("model_name", DEFAULT_SETTINGS["model_name"])

# Load MCP settings
if "enable_mcp" not in st.session_state:
    st.session_state.enable_mcp = settings.get("enable_mcp", DEFAULT_SETTINGS["enable_mcp"])
if "mcp_settings" not in st.session_state:
    st.session_state.mcp_settings = mcp_settings
if "editing_mcp_settings" not in st.session_state:
    st.session_state.editing_mcp_settings = False
if "mcp_processing" not in st.session_state:
    st.session_state.mcp_processing = False
if "mcp_tools_used" not in st.session_state:
    st.session_state.mcp_tools_used = []
# Initialize web search setting
if "enable_web_search" not in st.session_state:
    st.session_state.enable_web_search = settings.get("enable_web_search", DEFAULT_SETTINGS["enable_web_search"])

# Flag to track if we need to update the conversation history
if "update_conversation_history" not in st.session_state:
    st.session_state.update_conversation_history = False

# Set up web search and MCP toggles in sidebar
st.session_state.enable_web_search, st.session_state.enable_mcp = setup_sidebar_toggles(
    st.session_state.enable_web_search,
    st.session_state.enable_mcp,
    settings,
    save_settings
)

# Set up model settings in sidebar
st.session_state.reasoning_effort, st.session_state.show_reasoning, st.session_state.model_name = setup_sidebar_model_settings(
    st.session_state.reasoning_effort,
    st.session_state.show_reasoning,
    st.session_state.model_name,
    fetch_xai_models()[0],  # Get available models
    settings,
    save_settings
)

# Set up MCP settings UI if MCP is enabled
if st.session_state.enable_mcp:
    setup_mcp_settings_ui(
        st.session_state.enable_mcp,
        st.session_state.mcp_settings,
        get_mcp_server_descriptions(st.session_state.mcp_settings),
        save_mcp_settings
    )

# Create a new conversation button
if st.sidebar.button("New Conversation"):
    # Generate a new conversation ID
    new_conv_id = str(uuid.uuid4())

    # Set up the new conversation
    st.session_state.conversation_id = new_conv_id
    st.session_state.messages = create_new_conversation(
        st.session_state.conversations,
        new_conv_id
    )
    st.session_state.conversation_title = "New Conversation"

    # Set the update flag
    st.session_state.update_conversation_history = True

    # Rerun to update the UI
    st.rerun()

# Display conversation history in sidebar
if st.session_state.update_conversation_history:
    # Reload conversations from file to ensure we have the latest data
    st.session_state.conversations = load_conversations()
    st.session_state.update_conversation_history = False

# Display conversation history with rename and delete functionality
updated = display_conversation_history(
    st.session_state.conversations,
    st.session_state.conversation_id,
    st.session_state.conversation_title,
    st.session_state.messages,
    save_conversation
)

# Rerun if conversation history was updated
if updated:
    st.rerun()

# Main chat interface
st.title("Chat with Grok")
st.subheader(st.session_state.conversation_title)

# Display chat messages
for message in st.session_state.messages:
    if message["role"] != "system":
        display_chat_message(
            message,
            st.session_state.show_reasoning,
            get_mcp_tool_descriptions()
        )

# Chat input
prompt = st.chat_input("Ask Grok something...")

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        render_markdown_with_latex(prompt)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        # Show thinking indicator
        message_placeholder, thinking_container, tool_status_placeholder = show_thinking_indicator(st.session_state.enable_mcp)

        # Store the tool status placeholder in session state for use by MCP module
        st.session_state.tool_status_placeholder = tool_status_placeholder

        # If this is the first message, set the conversation title based on user input
        if len([m for m in st.session_state.messages if m["role"] == "user"]) == 1:
            st.session_state.conversation_title = prompt[:30] + "..." if len(prompt) > 30 else prompt

        # Generate response from Grok with enhanced Brave Search integration and MCP if enabled
        # Respect the web search toggle setting even when MCP is enabled
        full_response = generate_response(
            user_message=prompt,
            use_search=st.session_state.enable_web_search,
            reasoning_effort=st.session_state.reasoning_effort,
            use_mcp=st.session_state.enable_mcp
        )

        # Update the tool status placeholder to show completion
        if 'tool_status_placeholder' in st.session_state:
            if st.session_state.enable_mcp and full_response.get("mcp_tools_used"):
                tools_used = ", ".join(full_response["mcp_tools_used"])

                # Show tool results summary
                if hasattr(st.session_state, 'mcp_tool_results') and st.session_state.mcp_tool_results:
                    tool_count = len(st.session_state.mcp_tool_results)
                    result_count = sum(1 for result in st.session_state.mcp_tool_results if result["success"])
                    st.session_state.tool_status_placeholder.success(f"✅ Response generated using {result_count} successful tool results from: {tools_used}")
                else:
                    st.session_state.tool_status_placeholder.success(f"✅ Response generated using: {tools_used}")

                time.sleep(0.5)  # Give users time to see which tools were used

            # Now clear the status
            st.session_state.tool_status_placeholder.empty()

        # Display the response
        message_placeholder.empty()
        render_markdown_with_latex(full_response["content"])

        # Show reasoning if enabled
        if st.session_state.show_reasoning and full_response["reasoning"]:
            with st.expander("View Reasoning"):
                render_markdown_with_latex(full_response["reasoning"])

        # Add assistant response to chat history
        message_data = {
            "role": "assistant",
            "content": full_response["content"],
            "reasoning": full_response["reasoning"]
        }

        # Add MCP tools used if any
        if st.session_state.enable_mcp and full_response.get("mcp_tools_used"):
            message_data["mcp_tools_used"] = full_response["mcp_tools_used"]

            # Add tool results if available
            if hasattr(st.session_state, 'mcp_tool_results') and st.session_state.mcp_tool_results:
                message_data["mcp_tool_results"] = st.session_state.mcp_tool_results

        st.session_state.messages.append(message_data)

        # Save the conversation
        save_conversation(
            st.session_state.conversations,
            st.session_state.conversation_id,
            st.session_state.messages,
            st.session_state.conversation_title
        )

        # Set a flag to indicate that we need to update the conversation history
        st.session_state.update_conversation_history = True

        # Force a rerun to update the UI with the new conversation
        st.rerun()
