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
        "chat_perplexity_perplexity-mcp": "Conversational AI from Perplexity",
        "breakdown_complex_task_mcp-reasoner": "Break down complex tasks into manageable steps",
        "solve_equations_mcp-reasoner": "Solve mathematical equations and formulas",
        "analyze_problem_mcp-reasoner": "Analyze complex problems with structured reasoning"
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
        # Create a list of default tools, excluding Brave Search if it's disabled
        default_tools = []

        # Only add Brave Search if it's not explicitly disabled
        brave_search_disabled = False
        if "mcpServers" in st.session_state.mcp_settings and "brave-search" in st.session_state.mcp_settings["mcpServers"]:
            brave_search_disabled = st.session_state.mcp_settings["mcpServers"]["brave-search"].get("disabled", False)

        if not brave_search_disabled:
            default_tools.append("search_brave-search")

        # Add other default tools
        default_tools.extend([
            "tavily-search_tavily-mcp",
            "get_documentation_perplexity-mcp",
            "firecrawl_scrape_firecrawl-mcp",
            "deep-research_Serper-search-mcp"
        ])

        available_tools = default_tools

    return available_tools

def get_available_mcp_servers():
    """
    Get a list of available MCP servers based on the current MCP settings.

    Returns:
        list: List of available MCP server names
    """
    available_servers = []

    # Extract available servers from MCP settings
    if "mcpServers" in st.session_state.mcp_settings:
        for server_name, server_config in st.session_state.mcp_settings["mcpServers"].items():
            # Skip disabled servers
            if server_config.get("disabled", False):
                continue

            # Add server to available servers list
            available_servers.append(server_name)

    return available_servers

def get_mcp_system_instructions():
    """
    Generate system instructions about available MCP tools.

    Returns:
        str: System instructions about available MCP tools
    """
    available_servers = get_available_mcp_servers()
    available_tools = get_available_mcp_tools()

    if not available_servers:
        return ""

    # Create instructions about available MCP tools
    instructions = "\n\nAvailable MCP tools:\n"

    # Add information about each server
    for server in available_servers:
        # Get tools for this server
        server_tools = [t for t in available_tools if server in t]

        if server_tools:
            # Get server description from config if available
            from config import MCP_SERVER_DESCRIPTIONS
            server_desc = MCP_SERVER_DESCRIPTIONS.get(server, f"{server} integration")

            # Add server information
            instructions += f"- {server}: {server_desc}\n"

            # Add tool information for this server
            tool_descriptions = get_mcp_tool_descriptions()
            for tool in server_tools:
                tool_desc = tool_descriptions.get(tool, tool.replace("_", " ").capitalize())
                instructions += f"  - {tool}: {tool_desc}\n"

    # Add usage instructions
    instructions += "\nTo use a specific MCP tool, include 'Use [tool-name]' in your query. For example: 'Use mcp-reasoner to solve this equation'.\n"

    return instructions

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

    # Don't show any processing message initially - only show when a tool is actually used
    time.sleep(0.5)  # Small delay for initialization

    # Get available MCP tools and servers
    available_tools = get_available_mcp_tools()
    available_servers = get_available_mcp_servers()

    # Check if the user explicitly requested a specific MCP tool
    explicit_tool_request = None
    query_lower = query.lower()

    # Check for explicit MCP tool requests in the query
    for server in available_servers:
        if f"use {server.lower()}" in query_lower:
            explicit_tool_request = server
            break

    # If there's an explicit tool request, prioritize it
    if explicit_tool_request:
        # Find all tools from the requested MCP server
        requested_tools = [t for t in available_tools if explicit_tool_request in t]

        if requested_tools:
            # For mcp-reasoner, select the appropriate function based on the query
            if explicit_tool_request == "mcp-reasoner":
                if "breakdown" in query_lower or "complex task" in query_lower:
                    reasoner_tools = [t for t in requested_tools if "breakdown_complex_task" in t]
                    if reasoner_tools:
                        status_placeholder.info(f"Using MCP Reasoner for complex task breakdown...")
                        time.sleep(1.5)
                        tools_used.append(reasoner_tools[0])
                elif "equation" in query_lower or "formula" in query_lower or "math" in query_lower:
                    reasoner_tools = [t for t in requested_tools if "solve_equations" in t]
                    if reasoner_tools:
                        status_placeholder.info(f"Using MCP Reasoner for equation solving...")
                        time.sleep(1.5)
                        tools_used.append(reasoner_tools[0])
                else:
                    # Default to the first available reasoner tool
                    status_placeholder.info(f"Using MCP Reasoner...")
                    time.sleep(1.5)
                    tools_used.append(requested_tools[0])
            else:
                # For other MCP servers, just use the first available tool
                status_placeholder.info(f"Using requested MCP tool: {explicit_tool_request}...")
                time.sleep(1.5)
                tools_used.append(requested_tools[0])

            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

            # If we've found and used the explicitly requested tool, we can skip the rest
            # of the tool selection logic unless it's a search tool (we might want both)
            if not "search" in requested_tools[0].lower():
                # Show completion message if tools were used
                if tools_used:
                    status_placeholder.success("Processing complete")
                    time.sleep(0.5)

                # Always clear the status message
                status_placeholder.empty()
                return tools_used

    # If no explicit tool was requested or we want to add more tools,
    # continue with the regular tool selection logic

    # Try to use search for any query if available, web search is enabled, and no tools have been selected yet
    if not tools_used and st.session_state.get("enable_web_search", False):
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

    # Check for complex tasks, equations, or physics problems that would benefit from mcp-reasoner
    if ("equation" in query_lower or "formula" in query_lower or
        "physics" in query_lower or "mathematics" in query_lower or
        "complex task" in query_lower or "breakdown" in query_lower or
        "over-unity" in query_lower or "parametric" in query_lower):

        reasoner_tools = [t for t in available_tools if "mcp-reasoner" in t]
        if reasoner_tools:
            # Select the appropriate reasoner function
            if "breakdown" in query_lower or "complex task" in query_lower:
                breakdown_tools = [t for t in reasoner_tools if "breakdown_complex_task" in t]
                if breakdown_tools:
                    status_placeholder.info("Breaking down complex task...")
                    time.sleep(2)  # Simulate processing time
                    tools_used.append(breakdown_tools[0])
            elif "equation" in query_lower or "formula" in query_lower:
                equation_tools = [t for t in reasoner_tools if "solve_equations" in t]
                if equation_tools:
                    status_placeholder.info("Solving equations...")
                    time.sleep(2)  # Simulate processing time
                    tools_used.append(equation_tools[0])
            else:
                # Default to the first available reasoner tool
                status_placeholder.info("Analyzing problem with MCP Reasoner...")
                time.sleep(2)  # Simulate processing time
                tools_used.append(reasoner_tools[0])

            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Add news-specific tools for news-related queries
    if ("news" in query_lower or "latest" in query_lower or "recent" in query_lower):
        news_tools = [t for t in available_tools if "news" in t.lower() or "tavily" in t.lower()]
        if news_tools and news_tools[0] not in tools_used:
            status_placeholder.info("Retrieving latest news...")
            time.sleep(1.5)  # Simulate processing time
            tools_used.append(news_tools[0])
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Add code-specific tools for code-related queries
    if "code" in query_lower or "programming" in query_lower:
        code_tools = [t for t in available_tools if "documentation" in t.lower() or "perplexity" in t.lower()]
        if code_tools and code_tools[0] not in tools_used:
            status_placeholder.info("Retrieving code documentation...")
            time.sleep(1.5)  # Simulate processing time
            tools_used.append(code_tools[0])
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Add web-specific tools for web-related queries
    if "web" in query_lower or "website" in query_lower or "crawl" in query_lower:
        web_tools = [t for t in available_tools if "scrape" in t.lower() or "crawl" in t.lower() or "firecrawl" in t.lower()]
        if web_tools and web_tools[0] not in tools_used:
            status_placeholder.info("Crawling website content...")
            time.sleep(1.5)  # Simulate processing time
            tools_used.append(web_tools[0])
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Add research-specific tools for research-related queries
    if "research" in query_lower or "analyze" in query_lower or "disaster" in query_lower:
        research_tools = [t for t in available_tools if "research" in t.lower() or "serper" in t.lower()]
        if research_tools and research_tools[0] not in tools_used:
            status_placeholder.info("Performing deep research...")
            time.sleep(2)  # Simulate processing time
            tools_used.append(research_tools[0])
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Only show completion message if tools were actually used
    if tools_used:
        status_placeholder.success("Processing complete")
        time.sleep(0.5)  # Give user time to see the final status

    # Always clear the status message at the end
    status_placeholder.empty()

    return tools_used
