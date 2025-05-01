"""
UI module for the Grok Chat application.
Contains UI utility functions and components.
"""
import streamlit as st
import time
import json

def render_markdown_with_latex(text):
    """
    Render markdown text with LaTeX equations using st.markdown.
    Supports both block ($$...$$) and inline ($...$) equations.

    Args:
        text (str): Text to render
    """
    st.markdown(text, unsafe_allow_html=False)

def display_with_copy_option(text, _=None):
    """
    Display content with a copy option using Streamlit's built-in components.

    Args:
        text (str): The text to display and make available for copying
        _ (any, optional): Unused parameter (kept for backward compatibility)
    """
    # Display the text normally first
    st.markdown(text, unsafe_allow_html=False)

    # Add an expander for copying the text (without key parameter)
    with st.expander("Copy this response"):
        # Code block has built-in copy button
        st.code(text, language=None)

def display_chat_message(message, show_reasoning=False, tool_descriptions=None):
    """
    Display a chat message with optional reasoning and MCP tools used.

    Args:
        message (dict): Message object to display
        show_reasoning (bool, optional): Whether to show reasoning. Defaults to False.
        tool_descriptions (dict, optional): Descriptions of MCP tools. Defaults to None.
    """
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            # Render message content with copy option for assistant
            if message["role"] == "assistant":
                display_with_copy_option(message["content"])
            else:
                render_markdown_with_latex(message["content"])

            # Show reasoning if available and enabled
            if message.get("reasoning") and show_reasoning:
                with st.expander("View Reasoning"):
                    render_markdown_with_latex(message["reasoning"])

            # Show MCP tools used if available
            if message.get("mcp_tools_used") and len(message["mcp_tools_used"]) > 0:
                with st.expander("MCP Tools Used"):
                    st.markdown("### Tools Used for This Response")
                    # Display tools with descriptions in a compact format
                    for tool in message["mcp_tools_used"]:
                        description = tool_descriptions.get(tool, "External tool integration") if tool_descriptions else "External tool integration"
                        st.markdown(f"**{tool}**: {description}")

                    # Display tool results if available in the message
                    if message.get("mcp_tool_results"):
                        st.markdown("---")
                        st.markdown("### Tool Results")
                        for result in message["mcp_tool_results"]:
                            st.markdown(f"**Tool**: {result['tool']}")
                            if result["success"]:
                                if isinstance(result['data'], list):
                                    st.markdown("**Results**:")
                                    for i, item in enumerate(result['data'][:3]):  # Show only first 3 results
                                        if isinstance(item, dict):
                                            st.markdown(f"- {item.get('title', 'No title')}")
                                    if len(result['data']) > 3:
                                        st.caption(f"...and {len(result['data']) - 3} more results")
                                elif isinstance(result['data'], dict) and 'success' in result['data'] and result['data']['success']:
                                    # Format web scraping results
                                    if 'url' in result['data'] and 'title' in result['data'] and 'content' in result['data']:
                                        # Single page scrape result
                                        st.markdown(f"**Scraped content from**: [{result['data']['title']}]({result['data']['url']})")

                                        # Show content directly with a toggle button
                                        show_content_key = f"show_scraped_content_{result['tool']}_{id(result)}"
                                        if show_content_key not in st.session_state:
                                            st.session_state[show_content_key] = False

                                        # Toggle button to show/hide content
                                        if st.button("Toggle Scraped Content", key=f"toggle_{show_content_key}"):
                                            st.session_state[show_content_key] = not st.session_state[show_content_key]

                                        # Display content if toggled on
                                        if st.session_state[show_content_key]:
                                            st.markdown("**Scraped Content:**")
                                            st.markdown(result['data']['content'])

                                            # Add links if available
                                            if 'links' in result['data'] and result['data']['links']:
                                                st.markdown("**Links from the page:**")
                                                for i, link in enumerate(result['data']['links'][:5]):
                                                    st.markdown(f"- [{link.get('text', 'Link')}]({link.get('url', '')})")

                                    elif 'pages' in result['data'] and result['data']['pages']:
                                        # Multi-page crawl result
                                        st.markdown(f"**Crawled content from**: {result['data']['base_url']}")
                                        st.markdown(f"**Pages crawled**: {len(result['data']['pages'])}")

                                        # Show content directly with a toggle button
                                        show_content_key = f"show_crawled_content_{result['tool']}_{id(result)}"
                                        if show_content_key not in st.session_state:
                                            st.session_state[show_content_key] = False

                                        # Toggle button to show/hide content
                                        if st.button("Toggle Crawled Content", key=f"toggle_{show_content_key}"):
                                            st.session_state[show_content_key] = not st.session_state[show_content_key]

                                        # Display content if toggled on
                                        if st.session_state[show_content_key]:
                                            st.markdown("**Crawled Content:**")
                                            for i, page in enumerate(result['data']['pages'][:3]):
                                                st.markdown(f"**Page {i+1}**: [{page.get('title', 'No title')}]({page.get('url', 'No URL')})")
                                                st.markdown(page.get('content', 'No content available'))
                                                st.markdown("---")
                                    else:
                                        st.markdown(f"**Result**: {str(result['data'])[:100]}...")
                                else:
                                    st.markdown(f"**Result**: {str(result['data'])[:100]}...")
                            else:
                                st.markdown(f"**Error**: {result['error']}")
                            st.markdown("---")
                    # Fallback to session state if message doesn't have tool results
                    elif "mcp_tool_results" in st.session_state and st.session_state.mcp_tool_results:
                        st.markdown("---")
                        st.markdown("### Tool Results")
                        for result in st.session_state.mcp_tool_results:
                            st.markdown(f"**Tool**: {result['tool']}")
                            if result["success"]:
                                if isinstance(result['data'], list):
                                    st.markdown("**Results**:")
                                    for i, item in enumerate(result['data'][:3]):  # Show only first 3 results
                                        if isinstance(item, dict):
                                            st.markdown(f"- {item.get('title', 'No title')}")
                                    if len(result['data']) > 3:
                                        st.caption(f"...and {len(result['data']) - 3} more results")
                                elif isinstance(result['data'], dict) and 'success' in result['data'] and result['data']['success']:
                                    # Format web scraping results
                                    if 'url' in result['data'] and 'title' in result['data'] and 'content' in result['data']:
                                        # Single page scrape result
                                        st.markdown(f"**Scraped content from**: [{result['data']['title']}]({result['data']['url']})")

                                        # Show content directly with a toggle button
                                        show_content_key = f"show_scraped_content_{result['tool']}_{id(result)}"
                                        if show_content_key not in st.session_state:
                                            st.session_state[show_content_key] = False

                                        # Toggle button to show/hide content
                                        if st.button("Toggle Scraped Content", key=f"toggle_{show_content_key}"):
                                            st.session_state[show_content_key] = not st.session_state[show_content_key]

                                        # Display content if toggled on
                                        if st.session_state[show_content_key]:
                                            st.markdown("**Scraped Content:**")
                                            st.markdown(result['data']['content'])

                                            # Add links if available
                                            if 'links' in result['data'] and result['data']['links']:
                                                st.markdown("**Links from the page:**")
                                                for i, link in enumerate(result['data']['links'][:5]):
                                                    st.markdown(f"- [{link.get('text', 'Link')}]({link.get('url', '')})")

                                    elif 'pages' in result['data'] and result['data']['pages']:
                                        # Multi-page crawl result
                                        st.markdown(f"**Crawled content from**: {result['data']['base_url']}")
                                        st.markdown(f"**Pages crawled**: {len(result['data']['pages'])}")

                                        # Show content directly with a toggle button
                                        show_content_key = f"show_crawled_content_{result['tool']}_{id(result)}"
                                        if show_content_key not in st.session_state:
                                            st.session_state[show_content_key] = False

                                        # Toggle button to show/hide content
                                        if st.button("Toggle Crawled Content", key=f"toggle_{show_content_key}"):
                                            st.session_state[show_content_key] = not st.session_state[show_content_key]

                                        # Display content if toggled on
                                        if st.session_state[show_content_key]:
                                            st.markdown("**Crawled Content:**")
                                            for i, page in enumerate(result['data']['pages'][:3]):
                                                st.markdown(f"**Page {i+1}**: [{page.get('title', 'No title')}]({page.get('url', 'No URL')})")
                                                st.markdown(page.get('content', 'No content available'))
                                                st.markdown("---")
                                    else:
                                        st.markdown(f"**Result**: {str(result['data'])[:100]}...")
                                else:
                                    st.markdown(f"**Result**: {str(result['data'])[:100]}...")
                            else:
                                st.markdown(f"**Error**: {result['error']}")
                            st.markdown("---")

                    st.caption("These tools were used to enhance the response with external data sources and capabilities.")

def show_thinking_indicator(enable_mcp=False):
    """
    Show a thinking indicator while processing a request.

    Args:
        enable_mcp (bool, optional): Whether MCP is enabled. Defaults to False.

    Returns:
        tuple: (message_placeholder, thinking_container, tool_status_placeholder) for updating later
    """
    # Create placeholders for the message and thinking indicators
    message_placeholder = st.empty()
    thinking_container = st.container()

    # Show a simple thinking message
    with thinking_container:
        message_placeholder.markdown("Processing your request...")

        # Create a placeholder for tool status updates with a default message
        tool_status_placeholder = st.empty()

        # If MCP is enabled, show a waiting message for tools
        if enable_mcp:
            tool_status_placeholder.info("Selecting appropriate tools...")

            # Add a small spinner
            with st.spinner(""):
                time.sleep(0.1)  # Just to ensure the spinner appears

    return message_placeholder, thinking_container, tool_status_placeholder

def setup_sidebar_model_settings(reasoning_effort, show_reasoning, model_name, available_models, settings, save_settings_fn):
    """
    Set up the model settings section in the sidebar.

    Args:
        reasoning_effort (str): Current reasoning effort setting
        show_reasoning (bool): Current show reasoning setting
        model_name (str): Current model name
        available_models (list): List of available models
        settings (dict): Current settings dictionary
        save_settings_fn (function): Function to save settings

    Returns:
        tuple: (updated_reasoning_effort, updated_show_reasoning, updated_model_name)
    """
    with st.sidebar.expander("Model Settings", expanded=False):
        # Reasoning effort radio buttons
        reasoning_options = ["Low", "Medium", "High"]
        selected_reasoning = st.radio(
            "Reasoning Effort",
            reasoning_options,
            index=reasoning_options.index(reasoning_effort.capitalize()),
            horizontal=True,
            key="reasoning_radio"
        )

        # Update reasoning effort if changed
        updated_reasoning_effort = reasoning_effort
        if selected_reasoning.lower() != reasoning_effort:
            updated_reasoning_effort = selected_reasoning.lower()
            settings["reasoning_effort"] = updated_reasoning_effort
            save_settings_fn(settings)

        # Show reasoning checkbox
        updated_show_reasoning = st.checkbox("Show Reasoning", value=show_reasoning)
        if updated_show_reasoning != show_reasoning:
            settings["show_reasoning"] = updated_show_reasoning
            save_settings_fn(settings)

        # Model selection dropdown
        with st.spinner("Loading models..."):
            # Add current model to available models if not already there
            if model_name not in available_models:
                available_models.append(model_name)

            updated_model_name = st.selectbox(
                "Model",
                options=available_models,
                index=available_models.index(model_name),
                help="Select a model to use for chat completions"
            )

            # Update model name if changed
            if updated_model_name != model_name:
                settings["model_name"] = updated_model_name
                save_settings_fn(settings)

    return updated_reasoning_effort, updated_show_reasoning, updated_model_name

def setup_sidebar_toggles(enable_web_search, enable_mcp, settings, save_settings_fn):
    """
    Set up the web search and MCP toggles in the sidebar.

    Args:
        enable_web_search (bool): Current web search setting
        enable_mcp (bool): Current MCP setting
        settings (dict): Current settings dictionary
        save_settings_fn (function): Function to save settings

    Returns:
        tuple: (updated_enable_web_search, updated_enable_mcp)
    """
    # Web Search Toggle
    updated_enable_web_search = st.sidebar.toggle(
        "Enable Web Search (Brave Search)",
        value=enable_web_search
    )

    # Save Web Search toggle state if changed
    if updated_enable_web_search != enable_web_search:
        settings["enable_web_search"] = updated_enable_web_search
        save_settings_fn(settings)

    # MCP Toggle
    updated_enable_mcp = st.sidebar.toggle(
        "Enable MCP (Model Context Protocol)",
        value=enable_mcp,
        help="Enable Model Context Protocol for enhanced AI capabilities"
    )

    # Save MCP toggle state if changed
    if updated_enable_mcp != enable_mcp:
        settings["enable_mcp"] = updated_enable_mcp
        save_settings_fn(settings)

    return updated_enable_web_search, updated_enable_mcp

def setup_mcp_settings_ui(enable_mcp, mcp_settings, mcp_server_descriptions, save_mcp_settings_fn):
    """
    Set up the MCP settings UI in the sidebar.

    Args:
        enable_mcp (bool): Whether MCP is enabled
        mcp_settings (dict): Current MCP settings
        mcp_server_descriptions (dict): Descriptions of MCP servers
        save_mcp_settings_fn (function): Function to save MCP settings

    Returns:
        bool: Whether any changes were made to MCP settings
    """
    if not enable_mcp:
        return False

    changes_made = False

    with st.sidebar.expander("MCP Settings", expanded=False):
        st.info("Configure Model Context Protocol settings here. This allows the AI to access external tools and data sources.")

        # Display available MCP servers as toggles
        if "mcpServers" in mcp_settings and mcp_settings["mcpServers"]:
            st.subheader("Available MCP Servers")

            # Create toggles for each MCP server
            for server_name, server_config in mcp_settings["mcpServers"].items():
                # Get current disabled state (default to False if not present)
                current_disabled = server_config.get("disabled", False)

                # Get description or use a default
                description = mcp_server_descriptions.get(server_name, "External tool integration")

                # Create a toggle for this server
                new_disabled = not st.toggle(
                    f"{server_name}",
                    value=not current_disabled,
                    help=description
                )

                # If the state changed, update the settings
                if new_disabled != current_disabled:
                    mcp_settings["mcpServers"][server_name]["disabled"] = new_disabled
                    changes_made = True

            # Save settings if changes were made
            if changes_made:
                save_mcp_settings_fn(mcp_settings)

            # Add note about external editing
            st.markdown("---")
            st.caption("For advanced configuration, edit the mcp_settings.json file directly.")
        else:
            # No MCP servers configured
            st.warning("No active MCP servers found. Configure your MCP servers below.")

            # Display configuration instructions
            import os
            from config import MCP_SETTINGS_FILE

            if os.path.exists(MCP_SETTINGS_FILE) or os.path.exists("@" + MCP_SETTINGS_FILE):
                st.markdown("""
                ### How to Configure MCP Servers

                1. Edit the `mcp_settings.json` or `@mcp_settings.json` file in the application directory
                2. Make sure your MCP servers are properly configured with valid paths and API keys
                3. Ensure at least one server is not disabled
                4. Restart the application to load the new settings
                """)
            else:
                st.markdown("""
                ### How to Configure MCP Servers

                A default `mcp_settings.json` file has been created for you. You need to:

                1. Edit the `mcp_settings.json` file in the application directory
                2. Configure your MCP servers with valid paths and API keys
                3. Restart the application to load the new settings

                Example configuration:
                ```json
                {
                  "mcpServers": {
                    "brave-search": {
                      "command": "node",
                      "args": ["path/to/brave-search/index.js"],
                      "env": {
                        "BRAVE_API_KEY": "your-api-key-here"
                      },
                      "disabled": false,
                      "autoApprove": ["search"],
                      "description": "Custom description for Brave Search"
                    }
                  }
                }
                ```

                For enhanced security, you can create a `@mcp_settings.json` file instead, which is excluded from version control.
                """)

    return changes_made

def display_conversation_history(conversations, conversation_id, conversation_title, messages, save_conversation_fn):
    """
    Display the conversation history in the sidebar with rename and delete functionality.

    Args:
        conversations (dict): Dictionary of all conversations
        conversation_id (str): Current conversation ID
        conversation_title (str): Current conversation title
        messages (list): Current messages list
        save_conversation_fn (function): Function to save conversation

    Returns:
        bool: Whether the conversation history was updated
    """
    st.sidebar.title("Conversation History")

    # Initialize session state variables for conversation management if not already present
    if "renaming_conversation_id" not in st.session_state:
        st.session_state.renaming_conversation_id = None
    if "rename_input" not in st.session_state:
        st.session_state.rename_input = ""
    if "deleting_conversation_id" not in st.session_state:
        st.session_state.deleting_conversation_id = None

    # Sort conversations by timestamp (newest first)
    sorted_conversations = sorted(
        conversations.items(),
        key=lambda x: x[1].get("timestamp", ""),
        reverse=True
    )

    # Flag to track if any changes were made
    updated = False

    # Display each conversation
    for conv_id, conv_data in sorted_conversations:
        with st.sidebar.container():
            cols = st.columns([6, 1, 1])

            # Select conversation (title as button)
            if cols[0].button(f"{conv_data['title']}", key=f"history_{conv_id}"):
                st.session_state.conversation_id = conv_id
                st.session_state.messages = conv_data["messages"]
                st.session_state.conversation_title = conv_data["title"]
                updated = True

            # Rename button
            if cols[1].button("✏️", key=f"rename_{conv_id}"):
                st.session_state.renaming_conversation_id = conv_id
                st.session_state.rename_input = conv_data["title"]

            # Delete button
            if cols[2].button("🗑️", key=f"delete_{conv_id}"):
                st.session_state.deleting_conversation_id = conv_id

            # Rename UI
            if st.session_state.renaming_conversation_id == conv_id:
                new_title = st.text_input(
                    "Rename Conversation",
                    st.session_state.rename_input,
                    key=f"rename_input_{conv_id}"
                )
                rename_cols = st.columns([1, 1])
                if rename_cols[0].button("Save", key=f"save_rename_{conv_id}"):
                    conversations[conv_id]["title"] = new_title
                    save_conversation_fn(
                        conversations,
                        conv_id,
                        conversations[conv_id]["messages"],
                        new_title
                    )
                    # If renaming current conversation, update session title
                    if conversation_id == conv_id:
                        st.session_state.conversation_title = new_title
                    st.session_state.renaming_conversation_id = None
                    updated = True
                if rename_cols[1].button("Cancel", key=f"cancel_rename_{conv_id}"):
                    st.session_state.renaming_conversation_id = None
                    st.session_state.rename_input = ""

            # Delete confirmation
            if st.session_state.deleting_conversation_id == conv_id:
                del_cols = st.columns([1, 1])
                del_cols[0].warning("Delete this conversation?")
                if del_cols[1].button("Confirm Delete", key=f"confirm_delete_{conv_id}"):
                    del conversations[conv_id]
                    # If deleting current conversation, reset to new
                    if conversation_id == conv_id:
                        import uuid
                        from conversation import get_default_system_message

                        new_id = str(uuid.uuid4())
                        st.session_state.conversation_id = new_id
                        st.session_state.messages = [get_default_system_message()]
                        st.session_state.conversation_title = "New Conversation"

                    # Save updated conversations
                    with open("conversations.json", "w") as f:
                        json.dump(conversations, f)

                    st.session_state.deleting_conversation_id = None
                    updated = True
                if del_cols[1].button("Cancel", key=f"cancel_delete_{conv_id}"):
                    st.session_state.deleting_conversation_id = None

    return updated
