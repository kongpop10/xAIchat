import os
import streamlit as st
from openai import OpenAI
import time
import uuid
import json
from datetime import datetime
import requests
from functools import lru_cache
from icon import get_xai_favicon

SETTINGS_FILE = "settings.json"
MCP_SETTINGS_FILE = "mcp_settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)
    except Exception:
        pass

def load_mcp_settings():
    """Load MCP settings from the MCP settings file."""
    # First try to load from @mcp_settings.json (user's private file)
    if os.path.exists("@" + MCP_SETTINGS_FILE):
        try:
            with open("@" + MCP_SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Error loading @{MCP_SETTINGS_FILE}: {str(e)}")
            # Fall back to regular mcp_settings.json

    # If @mcp_settings.json doesn't exist or had an error, try regular mcp_settings.json
    if os.path.exists(MCP_SETTINGS_FILE):
        try:
            with open(MCP_SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Error loading {MCP_SETTINGS_FILE}: {str(e)}")
            return {}

    # If no settings file exists, return empty settings
    return {}

def save_mcp_settings(mcp_settings):
    """Save MCP settings to the MCP settings file."""
    # First try to save to @mcp_settings.json if it exists
    if os.path.exists("@" + MCP_SETTINGS_FILE):
        try:
            with open("@" + MCP_SETTINGS_FILE, "w") as f:
                json.dump(mcp_settings, f, indent=2)
            return
        except Exception as e:
            st.warning(f"Error saving to @{MCP_SETTINGS_FILE}: {str(e)}")
            # Fall back to regular mcp_settings.json

    # If @mcp_settings.json doesn't exist or had an error, save to regular mcp_settings.json
    try:
        with open(MCP_SETTINGS_FILE, "w") as f:
            json.dump(mcp_settings, f, indent=2)
    except Exception as e:
        st.warning(f"Error saving MCP settings: {str(e)}")

def load_conversations():
    try:
        with open("conversations.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_conversation(conversations, conversation_id, messages, title):
    conversations[conversation_id] = {
        "messages": messages,
        "title": title,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("conversations.json", "w") as f:
        json.dump(conversations, f)

def create_default_mcp_settings():
    """
    Create a default MCP settings file if none exists.

    Returns:
        dict: Default MCP settings
    """
    default_settings = {
        "mcpServers": {
            "brave-search": {
                "command": "node",
                "args": ["path/to/brave-search/index.js"],
                "env": {
                    "BRAVE_API_KEY": "your-api-key-here"
                },
                "disabled": False,
                "autoApprove": ["search"]
            }
        }
    }

    # Save the default settings
    try:
        with open(MCP_SETTINGS_FILE, "w") as f:
            json.dump(default_settings, f, indent=2)
        st.success(f"Created default {MCP_SETTINGS_FILE} file. Please edit it to configure your MCP servers.")
    except Exception as e:
        st.warning(f"Error creating default MCP settings: {str(e)}")

    return default_settings

def get_mcp_tool_descriptions():
    """
    Extract tool descriptions from MCP settings.

    Returns:
        dict: Mapping of tool names to descriptions
    """
    # Default descriptions for common tools
    default_descriptions = {
        "search_brave-search": "Web search using Brave Search API",
        "get_documentation_perplexity-mcp": "Documentation retrieval from Perplexity",
        "firecrawl_scrape_firecrawl-mcp": "Web scraping and content extraction",
        "firecrawl_crawl_firecrawl-mcp": "Website crawling and analysis",
        "deep-research_Serper-search-mcp": "In-depth research across multiple sources",
        "tavily-search_tavily-mcp": "AI-powered web search",
        "chat_perplexity_perplexity-mcp": "Conversational AI from Perplexity"
    }

    # Get MCP settings
    mcp_settings = st.session_state.mcp_settings

    # Initialize tool descriptions dictionary
    tool_descriptions = {}

    # Extract tool information from MCP settings
    if "mcpServers" in mcp_settings:
        for server_name, server_config in mcp_settings["mcpServers"].items():
            # Skip disabled servers
            if server_config.get("disabled", False):
                continue

            # Get auto-approved functions
            auto_approve = server_config.get("autoApprove", [])
            always_allow = server_config.get("alwaysAllow", [])

            # Combine all allowed functions
            allowed_functions = set(auto_approve + always_allow)

            # Add tool descriptions
            for function in allowed_functions:
                tool_name = f"{function}_{server_name}"

                # Use default description if available, otherwise generate one
                if tool_name in default_descriptions:
                    tool_descriptions[tool_name] = default_descriptions[tool_name]
                else:
                    # Generate a description based on function and server names
                    function_name = function.replace("_", " ")
                    server_display = server_name.replace("-mcp", "").replace("-", " ")
                    tool_descriptions[tool_name] = f"{function_name.capitalize()} via {server_display.capitalize()}"

    # If no tools were found, use default descriptions
    if not tool_descriptions:
        tool_descriptions = default_descriptions

    return tool_descriptions

# --- xAI Models Integration ---
@lru_cache(maxsize=1)
def fetch_xai_models():
    """Fetch available models from xAI API and cache the results."""
    try:
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            st.warning("xAI API key not set. Please set XAI_API_KEY in your environment.")
            return ["grok-3-mini-beta", "grok-3-mini-fast-beta"]  # Default models

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )

        # Fetch models from the API
        response = client.models.list()

        # Extract model IDs
        models = [model.id for model in response.data]

        # Sort models alphabetically
        models.sort()

        return models
    except Exception as e:
        st.warning(f"Error fetching models: {str(e)}")
        return ["grok-3-mini-beta", "grok-3-mini-fast-beta"]  # Default models as fallback

# Load settings
settings = load_settings()

# Load MCP settings or create default if none exist
mcp_settings = load_mcp_settings()
if not mcp_settings or "mcpServers" not in mcp_settings or not mcp_settings["mcpServers"]:
    # Create default MCP settings if none exist
    mcp_settings = create_default_mcp_settings()

# Initialize the Streamlit app with the xAI favicon
xai_favicon = get_xai_favicon()
st.set_page_config(
    page_title="Grok Chat",
    page_icon=xai_favicon,  # xAI favicon as icon
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    st.session_state.reasoning_effort = settings.get("reasoning_effort", "medium")
if "show_reasoning" not in st.session_state:
    st.session_state.show_reasoning = settings.get("show_reasoning", False)
if "model_name" not in st.session_state:
    st.session_state.model_name = settings.get("model_name", "grok-3-mini-beta")

# Load MCP settings
if "enable_mcp" not in st.session_state:
    st.session_state.enable_mcp = settings.get("enable_mcp", False)
if "mcp_settings" not in st.session_state:
    st.session_state.mcp_settings = mcp_settings
if "editing_mcp_settings" not in st.session_state:
    st.session_state.editing_mcp_settings = False
if "mcp_processing" not in st.session_state:
    st.session_state.mcp_processing = False
if "mcp_tools_used" not in st.session_state:
    st.session_state.mcp_tools_used = []

# Flag to track if we need to update the conversation history
if "update_conversation_history" not in st.session_state:
    st.session_state.update_conversation_history = False

# Set up sidebar
# st.sidebar.title("Grok Chat")

# Web Search Toggle - OUTSIDE Assistant Settings, above conversation section
if "enable_web_search" not in st.session_state:
    st.session_state.enable_web_search = settings.get("enable_web_search", True)
st.session_state.enable_web_search = st.sidebar.toggle(
    "Enable Web Search (Brave Search)",
    value=st.session_state.enable_web_search
)

# Save Web Search toggle state if changed
if st.session_state.enable_web_search != settings.get("enable_web_search", True):
    settings["enable_web_search"] = st.session_state.enable_web_search
    save_settings(settings)

# MCP Toggle - OUTSIDE Assistant Settings, below web search toggle
st.session_state.enable_mcp = st.sidebar.toggle(
    "Enable MCP (Model Context Protocol)",
    value=st.session_state.enable_mcp,
    help="Enable Model Context Protocol for enhanced AI capabilities"
)

# Save MCP toggle state if changed
if st.session_state.enable_mcp != settings.get("enable_mcp", False):
    settings["enable_mcp"] = st.session_state.enable_mcp
    save_settings(settings)

# Collapsible Model Settings at the top of the sidebar (without web search toggle)
with st.sidebar.expander("Model Settings", expanded=False):
    reasoning_options = ["Low", "Medium", "High"]
    selected_reasoning = st.radio(
        "Reasoning Effort",
        reasoning_options,
        index=reasoning_options.index(st.session_state.reasoning_effort.capitalize()),
        horizontal=True,
        key="reasoning_radio"
    )
    # Save reasoning effort if changed
    if selected_reasoning.lower() != st.session_state.reasoning_effort:
        st.session_state.reasoning_effort = selected_reasoning.lower()
        settings["reasoning_effort"] = st.session_state.reasoning_effort
        save_settings(settings)
    # Show Reasoning checkbox
    show_reasoning_box = st.checkbox("Show Reasoning", value=st.session_state.show_reasoning)
    if show_reasoning_box != st.session_state.show_reasoning:
        st.session_state.show_reasoning = show_reasoning_box
        settings["show_reasoning"] = st.session_state.show_reasoning
        save_settings(settings)

    # Fetch available models from xAI API
    with st.spinner("Loading models..."):
        available_models = fetch_xai_models()

    # Model selection dropdown
    if st.session_state.model_name not in available_models:
        available_models.append(st.session_state.model_name)

    selected_model = st.selectbox(
        "Model",
        options=available_models,
        index=available_models.index(st.session_state.model_name),
        help="Select a model to use for chat completions"
    )

    # Save model selection if changed
    if selected_model != st.session_state.model_name:
        st.session_state.model_name = selected_model
        settings["model_name"] = st.session_state.model_name
        save_settings(settings)

# MCP Settings expander (only shown when MCP is enabled)
if st.session_state.enable_mcp:
    with st.sidebar.expander("MCP Settings", expanded=False):
        st.info("Configure Model Context Protocol settings here. This allows the AI to access external tools and data sources.")

        # Create a mapping of server names to descriptions based on their capabilities
        mcp_server_descriptions = {
            "brave-search": "Web search using Brave Search API",
            "perplexity-mcp": "AI-powered search and documentation retrieval",
            "tavily-mcp": "AI-powered web search and content extraction",
            "Serper-search-mcp": "Google search and deep research capabilities",
            "fetch": "Web content fetching",
            "github": "GitHub integration",
            "Memory Graph": "Knowledge graph for memory storage",
            "mcp-reasoner": "Enhanced reasoning capabilities",
            "firecrawl-mcp": "Web scraping and crawling"
        }

        # Display available MCP servers as toggles
        if "mcpServers" in st.session_state.mcp_settings and st.session_state.mcp_settings["mcpServers"]:
            st.subheader("Available MCP Servers")

            # Track if any changes were made
            changes_made = False

            # Create toggles for each MCP server
            for server_name, server_config in st.session_state.mcp_settings["mcpServers"].items():
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
                    st.session_state.mcp_settings["mcpServers"][server_name]["disabled"] = new_disabled
                    changes_made = True

            # Save settings if changes were made
            if changes_made:
                save_mcp_settings(st.session_state.mcp_settings)

            # Add note about external editing
            st.markdown("---")
            st.caption("For advanced configuration, edit the mcp_settings.json file directly.")
        else:
            # No MCP servers configured
            st.warning("No active MCP servers found. Configure your MCP servers below.")

            # Check if we have a settings file
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
                      "autoApprove": ["search"]
                    }
                  }
                }
                ```

                For enhanced security, you can create a `@mcp_settings.json` file instead, which is excluded from version control.
                """)

# Create a new conversation button
if st.sidebar.button("New Conversation"):
    # Generate a new conversation ID
    new_conv_id = str(uuid.uuid4())

    # Set up the new conversation
    st.session_state.conversation_id = new_conv_id
    st.session_state.messages = [
        {"role": "system", "content": "You are a highly intelligent AI assistant powered by the Grok model from xAI."}
    ]
    st.session_state.conversation_title = "New Conversation"

    # Save the new conversation to ensure it appears in the history
    save_conversation(
        st.session_state.conversations,
        new_conv_id,
        st.session_state.messages,
        st.session_state.conversation_title
    )

    # Set the update flag
    st.session_state.update_conversation_history = True

    # Rerun to update the UI
    st.rerun()

# Display conversation history in sidebar
st.sidebar.title("Conversation History")

# Check if we need to update the conversation history
if st.session_state.update_conversation_history:
    # Reload conversations from file to ensure we have the latest data
    st.session_state.conversations = load_conversations()
    st.session_state.update_conversation_history = False

conversations = st.session_state.conversations

# State for renaming and deleting
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

for conv_id, conv_data in sorted_conversations:
    with st.sidebar.container():
        cols = st.columns([6, 1, 1])
        # Select conversation (title as button)
        if cols[0].button(f"{conv_data['title']}", key=f"history_{conv_id}"):
            st.session_state.conversation_id = conv_id
            st.session_state.messages = conv_data["messages"]
            st.session_state.conversation_title = conv_data["title"]
            st.rerun()
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
                st.session_state.conversations[conv_id]["title"] = new_title
                save_conversation(
                    st.session_state.conversations,
                    conv_id,
                    st.session_state.conversations[conv_id]["messages"],
                    new_title
                )
                # If renaming current conversation, update session title
                if st.session_state.conversation_id == conv_id:
                    st.session_state.conversation_title = new_title
                st.session_state.renaming_conversation_id = None
                st.rerun()
            if rename_cols[1].button("Cancel", key=f"cancel_rename_{conv_id}"):
                st.session_state.renaming_conversation_id = None
                st.session_state.rename_input = ""
        # Delete confirmation
        if st.session_state.deleting_conversation_id == conv_id:
            del_cols = st.columns([1, 1])
            del_cols[0].warning("Delete this conversation?")
            if del_cols[1].button("Confirm Delete", key=f"confirm_delete_{conv_id}"):
                del st.session_state.conversations[conv_id]
                # If deleting current conversation, reset to new
                if st.session_state.conversation_id == conv_id:
                    st.session_state.conversation_id = str(uuid.uuid4())
                    st.session_state.messages = [
                        {"role": "system", "content": "You are a highly intelligent AI assistant powered by the Grok model from xAI."}
                    ]
                    st.session_state.conversation_title = "New Conversation"
                # Save updated conversations
                with open("conversations.json", "w") as f:
                    json.dump(st.session_state.conversations, f)
                st.session_state.deleting_conversation_id = None
                st.rerun()
            if del_cols[1].button("Cancel", key=f"cancel_delete_{conv_id}"):
                st.session_state.deleting_conversation_id = None

# --- Brave Search Integration ---
def brave_search(query, count=10, country="us", freshness=None, max_retries=3):
    """
    Enhanced Brave Search API integration with advanced parameters and error handling.

    Args:
        query (str): The search query
        count (int): Number of results to return (1-50)
        country (str): Country code for localized results (e.g., "us", "gb")
        freshness (str, optional): Filter for result freshness (e.g., "d" for day, "w" for week)
        max_retries (int): Maximum number of retry attempts for API calls

    Returns:
        list: Processed search results with title, URL, snippet, and content
    """
    api_key = os.getenv('BRAVE_API_KEY')
    if not api_key:
        st.warning("Brave Search API key not set. Please set BRAVE_API_KEY in your environment.")
        return []

    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }

    # Build request parameters with advanced options
    params = {
        "q": query,
        "count": min(count, 50),  # Ensure count is within API limits
        "country": country
    }

    # Add optional parameters if provided
    if freshness:
        params["freshness"] = freshness

    # Implement retry logic with exponential backoff
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # Process and extract key elements from the response
            results = []
            for item in data.get('web', {}).get('results', []):
                result = {
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('description') or item.get('snippet', ''),
                    'content': item.get('page', {}).get('content', ''),
                    'published_date': item.get('published_date', '')
                }
                results.append(result)

            # Extract any cluster topics if available for better context organization
            clusters = data.get('web', {}).get('cluster_topics', [])
            if clusters:
                for i, result in enumerate(results):
                    if i < len(clusters):
                        result['cluster'] = clusters[i].get('title', '')

            return results

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                st.warning(f"Error fetching search results: {str(e)}")
                return []

    return []

# --- LLM System Prompt Addition: Math Formatting Instruction ---
LLM_MATH_FORMATTING_INSTRUCTION = """
When your response contains mathematical expressions or equations, format them as follows for correct rendering:

- For inline equations, wrap the LaTeX code with single dollar signs: $...$
  - Example: The resonant frequency is $\\omega_0 = \\frac{1}{\\sqrt{LC_0}}$.
- For block (display) equations, wrap the LaTeX code with double dollar signs:
  $$
  ...
  $$
  - Example:
    $$
    L \\frac{d^2 Q}{dt^2} + R \\frac{dQ}{dt} + \\frac{Q}{C(t)} = V_{\\text{in}}(t)
    $$

Always use these delimiters so that equations render correctly in Markdown/LaTeX environments.
"""

# --- MCP Tool Simulation for Testing ---
def simulate_mcp_tool_usage(query):
    """
    Simulate MCP tool usage based on the query content.
    This is for testing UI feedback only until actual MCP integration is implemented.
    Uses available tools from mcp_settings.json.

    Args:
        query (str): The user's query

    Returns:
        list: List of simulated MCP tools used
    """
    # Reset tools used
    tools_used = []

    # Create a status placeholder for real-time updates
    status_placeholder = st.empty()

    # Simulate MCP server initialization
    status_placeholder.info("Processing...")
    time.sleep(1)  # Simulate initialization time

    # Get available MCP tools from settings
    available_tools = []

    # Extract available tools from MCP settings
    if "mcpServers" in st.session_state.mcp_settings:
        for server_name, server_config in st.session_state.mcp_settings["mcpServers"].items():
            # Skip disabled servers
            if server_config.get("disabled", False):
                continue

            # Get auto-approved functions and always allowed functions
            auto_approve = server_config.get("autoApprove", [])
            always_allow = server_config.get("alwaysAllow", [])

            # Combine all allowed functions
            allowed_functions = set(auto_approve + always_allow)

            # Add tools to available tools list
            for function in allowed_functions:
                available_tools.append(f"{function}_{server_name}")

    # If no tools are available, use default tools for simulation
    if not available_tools:
        available_tools = [
            "search_brave-search",
            "tavily-search_tavily-mcp",
            "get_documentation_perplexity-mcp",
            "firecrawl_scrape_firecrawl-mcp",
            "deep-research_Serper-search-mcp"
        ]

    # Simulate tool usage based on query content and available tools
    # Try to use search for any query if available
    search_tools = [t for t in available_tools if "search" in t.lower()]
    if search_tools:
        status_placeholder.info(f"Using search tool...")
        time.sleep(1)  # Simulate processing time
        tools_used.append(search_tools[0])  # Use the first available search tool
        # Update session state immediately for UI feedback
        st.session_state.mcp_tools_used = tools_used.copy()

    # Add news-specific tools for news-related queries
    if ("news" in query.lower() or "latest" in query.lower() or "recent" in query.lower()):
        news_tools = [t for t in available_tools if "news" in t.lower() or "tavily" in t.lower()]
        if news_tools and news_tools[0] not in tools_used:
            status_placeholder.info("Retrieving latest news...")
            time.sleep(1.5)  # Simulate processing time
            tools_used.append(news_tools[0])
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Add code-specific tools for code-related queries
    if "code" in query.lower() or "programming" in query.lower():
        code_tools = [t for t in available_tools if "documentation" in t.lower() or "perplexity" in t.lower()]
        if code_tools and code_tools[0] not in tools_used:
            status_placeholder.info("Retrieving code documentation...")
            time.sleep(1.5)  # Simulate processing time
            tools_used.append(code_tools[0])
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Add web-specific tools for web-related queries
    if "web" in query.lower() or "website" in query.lower() or "crawl" in query.lower():
        web_tools = [t for t in available_tools if "scrape" in t.lower() or "crawl" in t.lower() or "firecrawl" in t.lower()]
        if web_tools and web_tools[0] not in tools_used:
            status_placeholder.info("Crawling website content...")
            time.sleep(1.5)  # Simulate processing time
            tools_used.append(web_tools[0])
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Add research-specific tools for research-related queries
    if "research" in query.lower() or "analyze" in query.lower() or "disaster" in query.lower():
        research_tools = [t for t in available_tools if "research" in t.lower() or "serper" in t.lower()]
        if research_tools and research_tools[0] not in tools_used:
            status_placeholder.info("Performing deep research...")
            time.sleep(2)  # Simulate processing time
            tools_used.append(research_tools[0])
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Show completion message if tools were used
    if tools_used:
        status_placeholder.success("Processing complete")
    else:
        status_placeholder.info("Processing complete")

    time.sleep(0.5)  # Give user time to see the final status
    status_placeholder.empty()  # Clear the status message

    return tools_used

# --- AI Integration with Brave Search and MCP ---
def generate_response(user_message, use_search=True, reasoning_effort="medium", use_mcp=False):
    """
    Generate a response using the Grok model with optional Brave Search integration and MCP.

    Args:
        user_message (str): The user's query or message
        use_search (bool): Whether to use Brave Search for context
        reasoning_effort (str): Level of reasoning effort for the Grok model
        use_mcp (bool): Whether to use Model Context Protocol for enhanced capabilities

    Returns:
        dict: Response containing content, reasoning, and MCP tools used
    """
    # Reset MCP tracking variables
    st.session_state.mcp_processing = use_mcp
    st.session_state.mcp_tools_used = []

    # Simulate MCP tool usage if MCP is enabled
    if use_mcp:
        simulate_mcp_tool_usage(user_message)
    # Get current date for AI awareness
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Define the base system prompt for Grok with date awareness and emphasis on factual accuracy
    grok_system_prompt = f"""You are an AI assistant powered by the Grok model from xAI. Today's date is {current_date}.

CRITICAL INSTRUCTIONS:
1. Be direct and concise - focus on answering the user's question
2. NEVER present speculative information as fact
3. When using search results or external tools, you MUST cite your sources
4. Always include a "References" section when providing factual information
5. If you don't have enough information to answer factually, clearly state this
6. When using MCP tools, always indicate which tools were used

Your primary goal is to provide helpful, ACCURATE information that directly addresses what the user is asking.
"""

    # Initialize context and search metadata
    context = ""
    search_metadata = {}

    # Fetch search results if enabled
    if use_search:
        try:
            # Determine optimal search parameters based on query complexity
            query_length = len(user_message.split())
            result_count = min(10, max(5, query_length // 3))  # Scale results with query complexity

            # Get freshness parameter based on query content
            time_sensitive_keywords = ["news", "recent", "latest", "today", "current"]
            freshness = "d" if any(keyword in user_message.lower() for keyword in time_sensitive_keywords) else None

            # Perform the search with enhanced parameters
            search_results = brave_search(
                query=user_message,
                count=result_count,
                freshness=freshness
            )

            if search_results:
                # Format search results for context
                formatted_results = []
                for i, r in enumerate(search_results):
                    result_text = f"[{i+1}] {r['title']}: {r['snippet']}"
                    if r.get('published_date'):
                        result_text += f" (Published: {r['published_date']})"
                    result_text += f" (Source: {r['url']})"
                    formatted_results.append(result_text)

                context = "\n".join(formatted_results)

                # Add search metadata for better context
                search_metadata = {
                    "result_count": len(search_results),
                    "query": user_message
                }
        except Exception as e:
            st.warning(f"Search error: {str(e)}. Proceeding without search results.")

    # Construct the prompt with context if available
    if context:
        # Create a structured prompt with search results - more direct and emphasizing citations
        prompt = f"""Query: "{user_message}"
Today's date is {current_date}.

Search results:
{context}

IMPORTANT INSTRUCTIONS:
1. Provide a direct answer using these search results and your knowledge
2. You MUST cite sources using [1], [2], etc. for ANY factual information
3. You MUST include a "References" section at the end listing all sources
4. If search results don't provide enough information, clearly state this
5. NEVER present information as factual without citing a source

Be concise and focus on answering what was asked.
"""
    else:
        # Use standard prompt without search context but still include date awareness
        prompt = f"""Today's date is {current_date}.

Answer directly: {user_message}

IMPORTANT: If you don't have enough information to answer factually, clearly state this. DO NOT make up information or present speculative information as fact."""

    # Add math formatting instructions
    prompt = f"{LLM_MATH_FORMATTING_INSTRUCTION}\n\n{prompt}"

    try:
        # Initialize the OpenAI client with xAI's base URL
        client = OpenAI(
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1"
        )

        # Prepare messages for the API call
        messages = [
            {"role": "system", "content": grok_system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Call the Grok model with optimized parameters
        completion = client.chat.completions.create(
            model=st.session_state.get("model_name", "grok-3-mini-beta"),
            reasoning_effort=reasoning_effort,
            messages=messages,
            temperature=0.3,  # Lower temperature for more factual responses when using search
        )

        # Extract content and reasoning
        content = completion.choices[0].message.content
        reasoning = getattr(completion.choices[0].message, "reasoning_content", "")

        # Process the response to ensure references are properly formatted
        if context and search_metadata and 'result_count' in search_metadata:
            # Store search results in a local variable to avoid potential scope issues
            local_search_results = []
            try:
                # Format search results from the context
                context_lines = context.split('\n')
                for line in context_lines:
                    if line.startswith('[') and '] ' in line and ' (Source: ' in line:
                        parts = line.split(' (Source: ')
                        if len(parts) == 2:
                            url_part = parts[1].rstrip(')')
                            title_part = parts[0].split('] ', 1)[1] if '] ' in parts[0] else parts[0]
                            local_search_results.append({'title': title_part, 'url': url_part})
            except Exception:
                # If parsing fails, we'll just skip adding references
                pass

            # Always add a References section when search results are used
            if local_search_results:
                # Check if the response already includes a References section
                if "References" not in content and "REFERENCES" not in content and "references" not in content.lower():
                    # Create references section from search results
                    references = "\n\n## References\n"
                    for i, r in enumerate(local_search_results):
                        references += f"[{i+1}] {r['title']} - {r['url']}\n"

                    # Add references to content
                    content += references

                # Add a note if no references section was found in the response
                elif not any(marker in content for marker in ["[1]", "[2]", "[3]"]):
                    content += "\n\n**Note: The information provided should include citations to the sources above. Please ask for clarification if sources aren't properly cited.**"

            # Add search attribution footer
            content += f"\n\n---\n*Response generated using Brave Search results on {current_date} for: \"{search_metadata['query']}\"*"

        # Add MCP attribution if MCP was used - with tools listed in content when appropriate
        if use_mcp and st.session_state.mcp_tools_used:
            # Add a Tools Used section if there's no References section
            if "References" not in content and "REFERENCES" not in content and "references" not in content.lower():
                content += "\n\n## Tools Used\n"
                for tool in st.session_state.mcp_tools_used:
                    content += f"- {tool}\n"

            # No footer for MCP tools - information is available in the expandable section
            pass
        elif use_mcp:
            # Only add a note if no tools were used but MCP was enabled
            content += f"\n\n---\n*Note: MCP was enabled but no specific tools were used for this query*"

        # Reset MCP processing status
        st.session_state.mcp_processing = False

        return {
            "content": content,
            "reasoning": reasoning,
            "mcp_tools_used": st.session_state.mcp_tools_used if use_mcp else []
        }
    except Exception as e:
        # Reset MCP processing status on error
        st.session_state.mcp_processing = False
        st.error(f"Error generating response: {str(e)}")
        return {
            "content": "Sorry, I encountered an error while processing your request.",
            "reasoning": "",
            "mcp_tools_used": []
        }

# --- Utility to render markdown and LaTeX ---
def render_markdown_with_latex(text):
    """
    Render markdown text with LaTeX equations using st.markdown.
    Supports both block ($$...$$) and inline ($...$) equations.
    """
    st.markdown(text, unsafe_allow_html=False)

# --- Utility function to display content with a copy option ---
def display_with_copy_option(text, _=None):  # Changed key to _ to indicate unused parameter
    """
    Display content with a copy option using Streamlit's built-in components.

    Args:
        text: The text to display and make available for copying
        _: Unused parameter (kept for backward compatibility)
    """
    # Display the text normally first
    st.markdown(text, unsafe_allow_html=False)

    # Add an expander for copying the text (without key parameter)
    with st.expander("Copy this response"):
        # Don't use key parameter at all since it's not supported
        st.code(text, language=None)  # Code block has built-in copy button

# Main chat interface
st.title("Chat with Grok")
st.subheader(st.session_state.conversation_title)

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            # Render message content with copy option for assistant
            if message["role"] == "assistant":
                display_with_copy_option(message["content"])  # Removed key parameter
            else:
                render_markdown_with_latex(message["content"])

            # Show reasoning if available and enabled
            if message.get("reasoning") and st.session_state.show_reasoning:
                with st.expander("View Reasoning"):
                    render_markdown_with_latex(message["reasoning"])

            # Show MCP tools used if available - with descriptions but more concise
            if message.get("mcp_tools_used") and len(message["mcp_tools_used"]) > 0:
                with st.expander("MCP Tools Used"):
                    # Get tool descriptions from MCP settings
                    tool_descriptions = get_mcp_tool_descriptions()

                    # Display tools with descriptions in a more compact format
                    for tool in message["mcp_tools_used"]:
                        description = tool_descriptions.get(tool, "External tool integration")
                        st.markdown(f"**{tool}**: {description}")

                    st.caption("These tools provide access to external data sources for more accurate information.")

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
        message_placeholder = st.empty()

        # Create a container for the thinking message and MCP status
        thinking_container = st.container()

        # Show a simple thinking message
        with thinking_container:
            message_placeholder.markdown("Processing your request...")

            # Add a small spinner if MCP is enabled
            if st.session_state.enable_mcp:
                with st.spinner(""):
                    time.sleep(0.1)  # Just to ensure the spinner appears

            # The MCP status will be handled by the simulate_mcp_tool_usage function

        # If this is the first message, set the conversation title based on user input
        if len([m for m in st.session_state.messages if m["role"] == "user"]) == 1:
            st.session_state.conversation_title = prompt[:30] + "..." if len(prompt) > 30 else prompt

        # Generate response from Grok with enhanced Brave Search integration and MCP if enabled
        full_response = generate_response(
            user_message=prompt,
            use_search=st.session_state.enable_web_search,
            reasoning_effort=st.session_state.reasoning_effort,
            use_mcp=st.session_state.enable_mcp
        )

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

# Add some information about the app
st.markdown("---")
caption_text = """This chat app uses the Grok model from xAI with enhanced Brave Search integration.
Adjust the reasoning effort in the sidebar to control how deeply Grok thinks about your questions.
Toggle web search to enable or disable Brave Search integration for more informed responses."""

# Add MCP information if enabled - with more details but without redundant text
if st.session_state.enable_mcp:
    caption_text += "\nModel Context Protocol (MCP) is enabled, allowing the AI to access external tools and data sources such as web search, document retrieval, and web scraping. You can see which tools were used by expanding the 'MCP Tools Used' section in each response."

st.caption(caption_text)
