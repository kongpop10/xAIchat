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

settings = load_settings()

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

# Set up sidebar
# st.sidebar.title("Grok Chat")

# Web Search Toggle - OUTSIDE Assistant Settings, above conversation section
if "enable_web_search" not in st.session_state:
    st.session_state.enable_web_search = True
st.session_state.enable_web_search = st.sidebar.toggle(
    "Enable Web Search (Brave Search)",
    value=st.session_state.enable_web_search
)

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

# Create a new conversation button
if st.sidebar.button("New Conversation"):
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.messages = [
        {"role": "system", "content": "You are a highly intelligent AI assistant powered by the Grok model from xAI."}
    ]
    st.session_state.conversation_title = "New Conversation"
    st.rerun()

# Display conversation history in sidebar
st.sidebar.title("Conversation History")
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

# --- AI Integration with Brave Search ---
def generate_response(user_message, use_search=True, reasoning_effort="medium"):
    """
    Generate a response using the Grok model with optional Brave Search integration.

    Args:
        user_message (str): The user's query or message
        use_search (bool): Whether to use Brave Search for context
        reasoning_effort (str): Level of reasoning effort for the Grok model

    Returns:
        dict: Response containing content and reasoning
    """
    # Get current date for AI awareness
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Define the base system prompt for Grok with date awareness
    grok_system_prompt = f"""You are an AI assistant analyzing Brave Search results. Today's date is {current_date}.
Process these key elements from each result:
1. Core factual claims
2. Statistical data points
3. Authoritative sources
4. Conflicting viewpoints

When providing information from search results, maintain factual accuracy and proper source attribution.
Always include numbered citations in your response when referencing search results.
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
        # Create a structured prompt with search results
        prompt = f"""You are an AI assistant analyzing Brave Search results for the query: "{user_message}"
Today's date is {current_date}.

Here are relevant search results:
{context}

Based on these results and your knowledge, provide a comprehensive answer to the user's query.
Synthesize information from multiple sources when available.
Acknowledge conflicting viewpoints if present.
Cite sources using [1], [2], etc. corresponding to the numbered search results.
If the search results don't contain sufficient information, clearly state what you know from your training.

IMPORTANT: At the end of your response, include a "References" section that lists all the sources you cited, using this format:
[1] Title of Source 1 - URL
[2] Title of Source 2 - URL
etc.
"""
    else:
        # Use standard prompt without search context but still include date awareness
        prompt = f"Today's date is {current_date}. {user_message}"

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

            # Check if the response already includes a References section
            if local_search_results and "References" not in content and "REFERENCES" not in content and "references" not in content.lower():
                # Create references section from search results
                references = "\n\n## References\n"
                for i, r in enumerate(local_search_results):
                    references += f"[{i+1}] {r['title']} - {r['url']}\n"

                # Add references to content
                content += references

            # Add search attribution footer
            content += f"\n\n---\n*Response generated using Brave Search results on {current_date} for: \"{search_metadata['query']}\"*"

        return {"content": content, "reasoning": reasoning}
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return {"content": "Sorry, I encountered an error while processing your request.", "reasoning": ""}

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
            if message.get("reasoning") and st.session_state.show_reasoning:
                with st.expander("View Reasoning"):
                    render_markdown_with_latex(message["reasoning"])

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
        message_placeholder.markdown("Thinking...")

        # If this is the first message, set the conversation title based on user input
        if len([m for m in st.session_state.messages if m["role"] == "user"]) == 1:
            st.session_state.conversation_title = prompt[:30] + "..." if len(prompt) > 30 else prompt

        # Generate response from Grok with enhanced Brave Search integration
        full_response = generate_response(
            user_message=prompt,
            use_search=st.session_state.enable_web_search,
            reasoning_effort=st.session_state.reasoning_effort
        )

        # Display the response
        message_placeholder.empty()
        render_markdown_with_latex(full_response["content"])

        # Show reasoning if enabled
        if st.session_state.show_reasoning and full_response["reasoning"]:
            with st.expander("View Reasoning"):
                render_markdown_with_latex(full_response["reasoning"])

        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response["content"],
            "reasoning": full_response["reasoning"]
        })

        # Save the conversation
        save_conversation(
            st.session_state.conversations,
            st.session_state.conversation_id,
            st.session_state.messages,
            st.session_state.conversation_title
        )

# Add some information about the app
st.markdown("---")
st.caption("""This chat app uses the Grok model from xAI with enhanced Brave Search integration.
Adjust the reasoning effort in the sidebar to control how deeply Grok thinks about your questions.
Toggle web search to enable or disable Brave Search integration for more informed responses.""")
