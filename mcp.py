"""
MCP module for the Grok Chat application.
Handles Model Context Protocol integration and simulation.
"""
import time
import streamlit as st

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

def get_available_mcp_tools():
    """
    Get a list of available MCP tools based on the current MCP settings.

    Returns:
        list: List of available MCP tool names
    """
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

    return available_tools

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

    # Get available MCP tools
    available_tools = get_available_mcp_tools()

    # Simulate tool usage based on query content and available tools
    # Try to use search for any query if available
    search_tools = [t for t in available_tools if "search" in t.lower()]
    if search_tools:
        status_placeholder.info(f"Using search tool...")
        time.sleep(1)  # Simulate processing time
        tools_used.append(search_tools[0])  # Use the first available search tool
        # Update session state immediately for UI feedback
        st.session_state.mcp_tools_used = tools_used.copy()

        # Store the fact that we're using search in session state
        # This will be used by the AI module to ensure search results are incorporated
        st.session_state.mcp_using_search = True

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
