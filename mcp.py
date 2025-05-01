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

        # Add firecrawl tools - prioritize these for web scraping
        firecrawl_tools = [
            "firecrawl_scrape_firecrawl-mcp",
            "firecrawl_crawl_firecrawl-mcp",
            "firecrawl_search_firecrawl-mcp",
            "firecrawl_map_firecrawl-mcp",
            "firecrawl_deep_research_firecrawl-mcp"
        ]
        default_tools.extend(firecrawl_tools)

        # Add other default tools
        default_tools.extend([
            "tavily-search_tavily-mcp",
            "get_documentation_perplexity-mcp",
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
            from config import get_mcp_server_descriptions
            server_desc = get_mcp_server_descriptions(st.session_state.mcp_settings).get(server, f"{server} integration")

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

def execute_mcp_tool(tool_name, query):
    """
    Execute an MCP tool and return the results.
    This function dynamically executes the appropriate MCP tool based on the tool name.

    Args:
        tool_name (str): The name of the tool to execute
        query (str): The user's query

    Returns:
        dict: The results from the tool execution
    """
    # Get the status placeholder from session state
    status_placeholder = st.session_state.get('tool_status_placeholder', st.empty())

    # Initialize result
    result = {
        "tool": tool_name,
        "success": False,
        "data": None,
        "error": None
    }

    try:
        # Extract the function name and server name from the tool name
        parts = tool_name.split('_', 1)
        if len(parts) != 2:
            result["error"] = f"Invalid tool name format: {tool_name}"
            return result

        function_name, server_name = parts

        # Show which tool is being executed
        status_placeholder.warning(f"🔍 Executing {function_name} with {server_name}...")

        # Special handling for Brave Search since it's directly implemented
        if server_name == "brave-search" and "search" in function_name.lower():
            # For Brave Search tools
            from search import brave_search

            # Determine if we need freshness parameter for news queries
            freshness = None
            if "news" in function_name.lower() or "latest" in query.lower():
                freshness = "d"  # Use day freshness for news

            # Execute the search
            search_results = brave_search(query=query, count=10, freshness=freshness)

            if search_results:
                result["success"] = True
                result["data"] = search_results
            else:
                result["error"] = "No search results found"

        # Special handling for firecrawl tools
        elif "firecrawl" in server_name:
            # Extract parameters based on the function type
            params = {}

            # For scraping, we need a URL
            if "scrape" in function_name.lower():
                # Extract URL from query - more comprehensive pattern
                import re

                # Try to find a URL with http/https or www
                url_match = re.search(r'https?://[^\s]+|www\.[^\s]+', query)

                # If not found, try to find a domain name pattern
                if not url_match:
                    domain_match = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\b', query)
                    if domain_match:
                        url_match = domain_match

                if url_match:
                    url = url_match.group(0)
                    # Ensure URL has proper protocol
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url

                    params = {
                        "url": url,
                        "formats": ["markdown"],  # Request markdown format for readability
                        "onlyMainContent": True   # Focus on main content
                    }

                # If we still don't have params, try to extract domain from query context
                if not params:
                    domain_keywords = ["website", "site", "page", "url", "link", "web", "content from", "information from", "data from", "scrape"]
                    for keyword in domain_keywords:
                        if keyword in query.lower():
                            # Look for words after the keyword that might be a domain
                            parts = query.lower().split(keyword)
                            if len(parts) > 1:
                                # Look for domain pattern in the text after the keyword
                                domain_match = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\b', parts[1])
                                if domain_match:
                                    potential_url = domain_match.group(0)
                                    # Ensure URL has proper protocol
                                    if not potential_url.startswith(('http://', 'https://')):
                                        potential_url = 'https://' + potential_url

                                    params = {
                                        "url": potential_url,
                                        "formats": ["markdown"],
                                        "onlyMainContent": True
                                    }
                                    break

                                # If no domain pattern found, try the first word
                                words = parts[1].strip().split()
                                if words:
                                    potential_url = words[0].strip('.,?!:;()[]{}\'\"')
                                    if '.' in potential_url:
                                        # Ensure URL has proper protocol
                                        if not potential_url.startswith(('http://', 'https://')):
                                            potential_url = 'https://' + potential_url

                                        params = {
                                            "url": potential_url,
                                            "formats": ["markdown"],
                                            "onlyMainContent": True
                                        }
                                        break

                    # No special handling for specific domains - we need a valid URL from the query

                # If we couldn't find a URL, return an error
                if not params:
                    result["error"] = "No valid URL found in the query. Please provide a URL to scrape."
                    return result

            # For crawling, we need a URL and depth parameters
            elif "crawl" in function_name.lower():
                # Extract URL from query - more comprehensive pattern
                import re

                # Try to find a URL with http/https or www
                url_match = re.search(r'https?://[^\s]+|www\.[^\s]+', query)

                # If not found, try to find a domain name pattern
                if not url_match:
                    domain_match = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\b', query)
                    if domain_match:
                        url_match = domain_match

                if url_match:
                    url = url_match.group(0)
                    # Ensure URL has proper protocol
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url

                    params = {
                        "url": url,
                        "maxDepth": 1,  # Limit depth to avoid excessive crawling
                        "limit": 5      # Limit number of pages
                    }
                else:
                    # Try to extract domain from query context
                    domain_keywords = ["website", "site", "page", "url", "link", "web", "crawl", "spider", "explore", "navigate"]
                    for keyword in domain_keywords:
                        if keyword in query.lower():
                            # Look for words after the keyword that might be a domain
                            parts = query.lower().split(keyword)
                            if len(parts) > 1:
                                # Look for domain pattern in the text after the keyword
                                domain_match = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\b', parts[1])
                                if domain_match:
                                    potential_url = domain_match.group(0)
                                    # Ensure URL has proper protocol
                                    if not potential_url.startswith(('http://', 'https://')):
                                        potential_url = 'https://' + potential_url

                                    params = {
                                        "url": potential_url,
                                        "maxDepth": 1,
                                        "limit": 5
                                    }
                                    break

                                # If no domain pattern found, try the first word
                                words = parts[1].strip().split()
                                if words:
                                    potential_url = words[0].strip('.,?!:;()[]{}\'\"')
                                    if '.' in potential_url:
                                        # Ensure URL has proper protocol
                                        if not potential_url.startswith(('http://', 'https://')):
                                            potential_url = 'https://' + potential_url

                                        params = {
                                            "url": potential_url,
                                            "maxDepth": 1,
                                            "limit": 5
                                        }
                                        break

                    # No special handling for specific domains - we need a valid URL from the query

                # If we couldn't find a URL, return an error
                if not params:
                    result["error"] = "No valid URL found in the query. Please provide a URL to crawl."
                    return result

            # For search, use the query directly
            elif "search" in function_name.lower():
                params = {
                    "query": query,
                    "limit": 10
                }

            # For deep research, use the query directly
            elif "deep_research" in function_name.lower():
                params = {
                    "query": query,
                    "maxDepth": 3
                }

            # Initialize result for firecrawl tools
            # Success will be set based on implementation status

            # Web scraping is not implemented
            if "scrape" in function_name.lower():
                url = params.get('url', '')
                result["success"] = False
                result["error"] = f"Web scraping for {url} is not implemented. Please check your MCP configuration."
            # Web crawling is not implemented
            elif "crawl" in function_name.lower():
                url = params.get('url', '')
                result["success"] = False
                result["error"] = f"Web crawling for {url} is not implemented. Please check your MCP configuration."
            # For search, use Brave Search API if available
            elif "search" in function_name.lower():
                query = params.get('query', '')

                # Check if this is a news-related query
                news_keywords = ["news", "latest", "recent", "current events", "today", "breaking"]
                is_news_query = any(keyword in query.lower() for keyword in news_keywords)

                # Use Brave Search API if available
                from search import brave_search

                # Set freshness parameter for news queries
                freshness = "d" if is_news_query else None

                # Execute the search with appropriate parameters
                search_results = brave_search(
                    query=query,
                    count=10,
                    freshness=freshness
                )

                if search_results:
                    result["data"] = search_results
                else:
                    result["success"] = False
                    result["error"] = "No search results found. Please check your search API configuration."
            # Deep research is not implemented
            elif "deep_research" in function_name.lower():
                query = params.get('query', '')
                result["success"] = False
                result["error"] = "Deep research integration is not implemented. Please check your MCP configuration."
            # Map functionality is not implemented
            elif "map" in function_name.lower():
                url = params.get('url', '')
                result["success"] = False
                result["error"] = "Map functionality is not implemented. Please check your MCP configuration."
            # Other firecrawl tools are not implemented
            else:
                result["success"] = False
                result["error"] = f"Firecrawl tool {function_name} is not implemented. Please check your MCP configuration."

        # Handle Tavily search tools - use Brave Search as a real search backend
        elif "tavily" in server_name and "search" in function_name.lower():
            params = {
                "query": query,
                "max_results": 10,
                "search_depth": "advanced" if "deep" in query.lower() else "basic"
            }

            # Check if this is a news-related query
            news_keywords = ["news", "latest", "recent", "current events", "today", "breaking"]
            is_news_query = any(keyword in query.lower() for keyword in news_keywords)

            # Use Brave Search API if available
            from search import brave_search

            # Set freshness parameter for news queries
            freshness = "d" if is_news_query else None

            # Execute the search with appropriate parameters
            search_results = brave_search(
                query=query,
                count=10,
                freshness=freshness
            )

            if search_results:
                result["success"] = True
                result["data"] = search_results
            else:
                result["success"] = False
                result["error"] = "No search results found. Please check your search API configuration."

        # Handle Perplexity tools
        elif "perplexity" in server_name:
            if "documentation" in function_name.lower():
                # Extract the technology from the query
                tech_keywords = ["python", "javascript", "react", "node", "java", "c++", "golang", "ruby", "php"]
                technology = next((tech for tech in tech_keywords if tech in query.lower()), "general")

                params = {
                    "query": technology,
                    "context": query
                }
            elif "search" in function_name.lower():
                params = {
                    "query": query,
                    "detail_level": "detailed" if "detailed" in query.lower() else "normal"
                }

                # Check if this is a news-related query
                news_keywords = ["news", "latest", "recent", "current events", "today", "breaking"]
                is_news_query = any(keyword in query.lower() for keyword in news_keywords)

                # Use Brave Search API if available
                from search import brave_search

                # Set freshness parameter for news queries
                freshness = "d" if is_news_query else None

                # Execute the search with appropriate parameters
                search_results = brave_search(
                    query=query,
                    count=10,
                    freshness=freshness
                )

                if search_results:
                    result["success"] = True
                    result["data"] = search_results
                else:
                    result["success"] = False
                    result["error"] = "No search results found. Please check your search API configuration."
            elif "chat" in function_name.lower():
                params = {
                    "message": query
                }

                # Perplexity chat is not implemented
                result["success"] = False
                result["error"] = "Perplexity chat integration is not implemented. Please check your MCP configuration."

        # Handle Serper search tools
        elif "serper" in server_name:
            if "deep-research" in function_name.lower():
                params = {
                    "query": query,
                    "depth": "standard"
                }
            else:
                params = {
                    "query": query
                }

            # Check if this is a news-related query
            news_keywords = ["news", "latest", "recent", "current events", "today", "breaking"]
            is_news_query = any(keyword in query.lower() for keyword in news_keywords)

            # Use Brave Search API if available
            from search import brave_search

            # Set freshness parameter for news queries
            freshness = "d" if is_news_query else None

            # Execute the search with appropriate parameters
            search_results = brave_search(
                query=query,
                count=10,
                freshness=freshness
            )

            if search_results:
                result["success"] = True
                result["data"] = search_results
            else:
                result["success"] = False
                result["error"] = "No search results found. Please check your search API configuration."

        # Handle MCP reasoner tools
        elif "mcp-reasoner" in server_name:
            # MCP reasoner is not implemented
            result["success"] = False
            result["error"] = "MCP reasoner integration is not implemented. Please check your MCP configuration."

        # For any other tools that might be search-related, try to use real search
        elif "search" in function_name.lower():
            status_placeholder.warning(f"🔍 Tool {tool_name} appears to be a search tool. Using search functionality...")

            # Check if this is a news-related query
            news_keywords = ["news", "latest", "recent", "current events", "today", "breaking"]
            is_news_query = any(keyword in query.lower() for keyword in news_keywords)

            # Use Brave Search API if available
            from search import brave_search

            # Set freshness parameter for news queries
            freshness = "d" if is_news_query else None

            # Execute the search with appropriate parameters
            search_results = brave_search(
                query=query,
                count=10,
                freshness=freshness
            )

            if search_results:
                result["success"] = True
                result["data"] = search_results
            else:
                result["success"] = False
                result["error"] = "No search results found. Please check your search API configuration."

        # For any other tools, return an error
        else:
            status_placeholder.warning(f"🔍 Tool {tool_name} is not specifically implemented.")
            result["success"] = False
            result["error"] = f"Tool {tool_name} is not implemented. Please check your MCP configuration."

    except Exception as e:
        result["error"] = str(e)
        status_placeholder.error(f"⚠️ Error executing tool {tool_name}: {str(e)}")

    return result

def select_mcp_tools(query):
    """
    Select appropriate MCP tools based on the query content.
    Uses available tools from mcp_settings.json.
    Intelligently selects tools based on query intent and available tools.

    Args:
        query (str): The user's query

    Returns:
        list: List of selected MCP tools
    """
    # Reset tools used
    tools_used = []

    # Use the tool status placeholder from session state if available, otherwise create a new one
    status_placeholder = st.session_state.get('tool_status_placeholder', st.empty())

    # Handle web scraping requests
    if "scrape" in query.lower():
        # Check for URL in query
        import re
        url_match = re.search(r'https?://[^\s]+|www\.[^\s]+', query)
        domain_match = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\b', query)

        # If URL is present or there's a domain name, use a scraping tool
        if url_match or domain_match or "content from" in query.lower() or "website" in query.lower():
            # Get available MCP tools and servers
            available_tools = get_available_mcp_tools()

            # Look for scraping tools
            scrape_tools = [t for t in available_tools if "scrape" in t.lower()]

            if scrape_tools:
                # Use the first available scraping tool
                tool_name = scrape_tools[0]
                status_placeholder.warning(f"🔍 Using web scraping tool: {tool_name}")
                tools_used.append(tool_name)
                # Update session state immediately for UI feedback
                st.session_state.mcp_tools_used = tools_used.copy()

                # Execute the tool immediately to ensure it's used
                result = execute_mcp_tool(tool_name, query)
                if result["success"]:
                    if not hasattr(st.session_state, 'mcp_tool_results'):
                        st.session_state.mcp_tool_results = []
                    st.session_state.mcp_tool_results.append(result)

                return tools_used

    # Direct check for crawling requests - high priority handling
    if "crawl" in query.lower():
        # Check for URL in query
        import re
        url_match = re.search(r'https?://[^\s]+|www\.[^\s]+', query)
        domain_match = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\b', query)

        # If URL is present or there's a domain name, use a crawling tool
        if url_match or domain_match or "website" in query.lower() or "site" in query.lower():
            # Get available MCP tools and servers
            available_tools = get_available_mcp_tools()

            # Look for crawling tools
            crawl_tools = [t for t in available_tools if "crawl" in t.lower()]

            if crawl_tools:
                # Use the first available crawling tool
                tool_name = crawl_tools[0]
                status_placeholder.warning(f"🔍 Using web crawling tool: {tool_name}")
                tools_used.append(tool_name)
                # Update session state immediately for UI feedback
                st.session_state.mcp_tools_used = tools_used.copy()

                # Execute the tool immediately to ensure it's used
                result = execute_mcp_tool(tool_name, query)
                if result["success"]:
                    if not hasattr(st.session_state, 'mcp_tool_results'):
                        st.session_state.mcp_tool_results = []
                    st.session_state.mcp_tool_results.append(result)

                return tools_used

    # Get available MCP tools and servers
    available_tools = get_available_mcp_tools()
    available_servers = get_available_mcp_servers()

    # If no tools are available, notify the user and return empty list
    if not available_tools:
        status_placeholder.error("⚠️ No MCP tools are available. Please check your MCP settings.")
        time.sleep(2)  # Give more time to see the error
        # Don't clear the status message here - it will be cleared by app.py
        return tools_used

    # Analyze query to determine intent
    query_lower = query.lower()

    # Define intent categories and their keywords
    intent_categories = {
        "web_scraping": ["scrape", "website", "webpage", "web page", "site content", "extract from site", "get content from", "content from", "information from", "data from", "text from", "extract content", "extract data", "extract information", "extract text", "get website", "get webpage", "get web page", "get site", "get page", "fetch website", "fetch webpage", "fetch web page", "fetch site", "fetch page", "retrieve website", "retrieve webpage", "retrieve web page", "retrieve site", "retrieve page"],
        "web_crawling": ["crawl", "spider", "website structure", "site map", "multiple pages", "scan website", "scan site", "scan web", "scan page", "explore website", "explore site", "explore web", "explore page", "navigate website", "navigate site", "navigate web", "navigate page"],
        "search": ["search", "find information", "look up", "find out", "information about", "what is", "who is", "where is", "when did", "how to", "why is", "can you", "tell me about", "explain", "describe", "define", "meaning of", "definition of", "information on", "details about", "facts about", "learn about"],
        "news": ["news", "latest", "recent", "current events", "today's headlines", "breaking", "current news", "recent developments", "latest updates", "current situation", "what's happening", "recent news", "today's news", "this week's news", "this month's news"],
        "documentation": ["documentation", "docs", "api", "library", "framework", "how to use", "code example", "programming", "coding", "developer", "development", "software", "application", "app", "program", "script", "function", "method", "class", "object", "variable", "constant", "parameter", "argument", "return value", "syntax", "semantics", "implementation", "interface", "module", "package", "dependency", "import", "export", "compile", "build", "deploy", "run", "execute", "debug", "test", "unit test", "integration test", "functional test", "performance test", "benchmark", "profiling", "optimization", "refactoring", "code review", "version control", "git", "svn", "mercurial", "repository", "commit", "push", "pull", "merge", "branch", "tag", "release", "deployment", "continuous integration", "continuous delivery", "continuous deployment", "devops", "agile", "scrum", "kanban", "waterfall", "lean", "extreme programming", "pair programming", "code quality", "code coverage", "code complexity", "code smell", "technical debt", "clean code", "design pattern", "architecture", "microservice", "monolith", "serverless", "cloud", "container", "docker", "kubernetes", "orchestration", "scaling", "load balancing", "high availability", "fault tolerance", "disaster recovery", "backup", "restore", "monitoring", "logging", "alerting", "metrics", "analytics", "dashboard", "visualization", "reporting", "business intelligence", "data science", "machine learning", "artificial intelligence", "deep learning", "neural network", "natural language processing", "computer vision", "speech recognition", "speech synthesis", "chatbot", "virtual assistant", "recommendation system", "personalization", "user experience", "user interface", "frontend", "backend", "full stack", "web development", "mobile development", "desktop development", "embedded development", "game development", "database", "sql", "nosql", "relational database", "document database", "key-value database", "graph database", "time series database", "in-memory database", "distributed database", "data warehouse", "data lake", "data mining", "data analysis", "data visualization", "data modeling", "data engineering", "data architecture", "data governance", "data quality", "data security", "data privacy", "data protection", "data backup", "data recovery", "data migration", "data integration", "data transformation", "data pipeline", "data streaming", "data batch processing", "data real-time processing", "data near-real-time processing", "data offline processing", "data online processing", "data analytics", "data science", "data scientist", "data engineer", "data analyst", "data architect", "data administrator", "database administrator", "database developer", "database designer", "database architect", "database engineer", "database analyst", "database administrator", "database security", "database performance", "database optimization", "database tuning", "database indexing", "database partitioning", "database sharding", "database replication", "database backup", "database recovery", "database migration", "database upgrade", "database downgrade", "database version control", "database schema", "database model", "database design", "database architecture", "database security", "database performance", "database optimization", "database tuning", "database indexing", "database partitioning", "database sharding", "database replication", "database backup", "database recovery", "database migration", "database upgrade", "database downgrade", "database version control", "database schema", "database model", "database design", "database architecture"],
        "research": ["research", "in-depth", "comprehensive", "analyze", "study", "investigate", "deep dive", "thorough", "detailed", "extensive", "exhaustive", "complete", "full", "comprehensive", "all-inclusive", "all-encompassing", "all-embracing", "all-around", "all-out", "all-over", "all-purpose", "all-round", "all-sided", "all-embracing", "all-encompassing", "all-inclusive", "all-around", "all-out", "all-over", "all-purpose", "all-round", "all-sided"],
        "reasoning": ["solve", "equation", "formula", "math", "physics", "breakdown", "complex task", "step by step", "analyze problem", "solution", "answer", "result", "output", "outcome", "conclusion", "finding", "discovery", "revelation", "insight", "understanding", "comprehension", "grasp", "mastery", "knowledge", "wisdom", "intelligence", "intellect", "mind", "brain", "thought", "thinking", "cognition", "perception", "conception", "idea", "notion", "concept", "theory", "hypothesis", "conjecture", "supposition", "assumption", "presumption", "premise", "postulate", "axiom", "theorem", "law", "rule", "principle", "guideline", "standard", "criterion", "measure", "benchmark", "yardstick", "touchstone", "litmus test", "acid test", "test", "trial", "experiment", "investigation", "examination", "inspection", "scrutiny", "review", "analysis", "evaluation", "assessment", "appraisal", "judgment", "verdict", "decision", "determination", "resolution", "conclusion", "finding", "discovery", "revelation", "insight", "understanding", "comprehension", "grasp", "mastery", "knowledge", "wisdom", "intelligence", "intellect", "mind", "brain", "thought", "thinking", "cognition", "perception", "conception", "idea", "notion", "concept", "theory", "hypothesis", "conjecture", "supposition", "assumption", "presumption", "premise", "postulate", "axiom", "theorem", "law", "rule", "principle", "guideline", "standard", "criterion", "measure", "benchmark", "yardstick", "touchstone", "litmus test", "acid test", "test", "trial", "experiment", "investigation", "examination", "inspection", "scrutiny", "review", "analysis", "evaluation", "assessment", "appraisal", "judgment", "verdict", "decision", "determination", "resolution", "conclusion", "finding", "discovery", "revelation", "insight", "understanding", "comprehension", "grasp", "mastery", "knowledge", "wisdom", "intelligence", "intellect", "mind", "brain", "thought", "thinking", "cognition", "perception", "conception", "idea", "notion", "concept", "theory", "hypothesis", "conjecture", "supposition", "assumption", "presumption", "premise", "postulate", "axiom", "theorem", "law", "rule", "principle", "guideline", "standard", "criterion", "measure", "benchmark", "yardstick", "touchstone", "litmus test", "acid test", "test", "trial", "experiment", "investigation", "examination", "inspection", "scrutiny", "review", "analysis", "evaluation", "assessment", "appraisal", "judgment", "verdict", "decision", "determination", "resolution"]
    }

    # Check if the user explicitly requested a specific MCP tool
    explicit_tool_request = None

    # Check for explicit MCP tool requests in the query
    for server in available_servers:
        if f"use {server.lower()}" in query_lower:
            explicit_tool_request = server
            break

    # Also check for explicit tool function requests
    explicit_function_request = None
    for category, keywords in intent_categories.items():
        for keyword in keywords:
            if f"use {keyword}" in query_lower:
                explicit_function_request = category
                break
        if explicit_function_request:
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
                        tool_name = reasoner_tools[0]
                        status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                        tools_used.append(tool_name)
                elif "equation" in query_lower or "formula" in query_lower or "math" in query_lower:
                    reasoner_tools = [t for t in requested_tools if "solve_equations" in t]
                    if reasoner_tools:
                        tool_name = reasoner_tools[0]
                        status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                        tools_used.append(tool_name)
                else:
                    # Default to the first available reasoner tool
                    tool_name = requested_tools[0]
                    status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                    tools_used.append(tool_name)
            # For firecrawl, select the appropriate function based on the query
            elif explicit_tool_request == "firecrawl-mcp":
                if any(keyword in query_lower for keyword in intent_categories["web_scraping"]):
                    scrape_tools = [t for t in requested_tools if "scrape" in t.lower()]
                    if scrape_tools:
                        tool_name = scrape_tools[0]
                        status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                        tools_used.append(tool_name)
                elif any(keyword in query_lower for keyword in intent_categories["web_crawling"]):
                    crawl_tools = [t for t in requested_tools if "crawl" in t.lower()]
                    if crawl_tools:
                        tool_name = crawl_tools[0]
                        status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                        tools_used.append(tool_name)
                else:
                    # Default to the first available firecrawl tool
                    tool_name = requested_tools[0]
                    status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                    tools_used.append(tool_name)
            else:
                # For other MCP servers, just use the first available tool
                tool_name = requested_tools[0]
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)

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
        else:
            # Requested tool not available
            status_placeholder.error(f"⚠️ Requested MCP tool '{explicit_tool_request}' is not available.")
            time.sleep(2)  # Give more time to see the error

    # If there's an explicit function request, find the appropriate tool
    if explicit_function_request and not tools_used:
        if explicit_function_request == "web_scraping":
            scrape_tools = [t for t in available_tools if "scrape" in t.lower()]
            if scrape_tools:
                tool_name = scrape_tools[0]
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)
        elif explicit_function_request == "web_crawling":
            crawl_tools = [t for t in available_tools if "crawl" in t.lower()]
            if crawl_tools:
                tool_name = crawl_tools[0]
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)
        elif explicit_function_request == "search":
            search_tools = [t for t in available_tools if "search" in t.lower()]
            if search_tools:
                tool_name = search_tools[0]
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)
        elif explicit_function_request == "news":
            news_tools = [t for t in available_tools if "news" in t.lower() or "tavily" in t.lower()]
            if news_tools:
                tool_name = news_tools[0]
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)
        elif explicit_function_request == "documentation":
            doc_tools = [t for t in available_tools if "documentation" in t.lower() or "perplexity" in t.lower()]
            if doc_tools:
                tool_name = doc_tools[0]
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)
        elif explicit_function_request == "research":
            research_tools = [t for t in available_tools if "research" in t.lower() or "serper" in t.lower()]
            if research_tools:
                tool_name = research_tools[0]
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)
        elif explicit_function_request == "reasoning":
            reasoning_tools = [t for t in available_tools if "mcp-reasoner" in t]
            if reasoning_tools:
                tool_name = reasoning_tools[0]
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)

        # Update session state immediately for UI feedback
        if tools_used:
            st.session_state.mcp_tools_used = tools_used.copy()
            return tools_used

    # If no explicit tool was requested or we want to add more tools,
    # continue with the intelligent tool selection logic

    # Detect URLs in the query - strong indicator for web scraping/crawling
    import re

    # More comprehensive URL detection
    url_match = re.search(r'https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}|[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}', query_lower)

    # Check for domain names without http/www prefix
    domain_match = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\b', query_lower)

    # Check for explicit web scraping intent
    has_scraping_intent = any(keyword in query_lower for keyword in intent_categories["web_scraping"])

    # If URL is present or there's explicit scraping intent, prioritize web scraping/crawling tools
    if (url_match or domain_match or has_scraping_intent) and not tools_used:
        # Look for firecrawl tools first
        firecrawl_tools = [t for t in available_tools if "firecrawl" in t.lower()]

        # If no firecrawl tools, look for any web tools
        if not firecrawl_tools:
            web_tools = [t for t in available_tools if "scrape" in t.lower() or "crawl" in t.lower()]
        else:
            web_tools = firecrawl_tools

        if web_tools:
            # Determine if we should scrape or crawl based on query context
            if any(keyword in query_lower for keyword in intent_categories["web_crawling"]):
                crawl_tools = [t for t in web_tools if "crawl" in t.lower()]
                if crawl_tools:
                    tool_name = crawl_tools[0]
                    status_placeholder.warning(f"🔍 Using web crawling tool: {tool_name}")
                    tools_used.append(tool_name)
                elif web_tools:  # If no specific crawl tool, use any web tool
                    tool_name = web_tools[0]
                    status_placeholder.warning(f"🔍 Using web tool: {tool_name}")
                    tools_used.append(tool_name)
            else:
                # Default to scraping for single URLs or explicit scraping requests
                scrape_tools = [t for t in web_tools if "scrape" in t.lower()]
                if scrape_tools:
                    tool_name = scrape_tools[0]
                    status_placeholder.warning(f"🔍 Using web scraping tool: {tool_name}")
                    tools_used.append(tool_name)
                elif web_tools:  # If no specific scrape tool, use any web tool
                    tool_name = web_tools[0]
                    status_placeholder.warning(f"🔍 Using web tool: {tool_name}")
                    tools_used.append(tool_name)

            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Try to use search for any query if available, web search is enabled, and no tools have been selected yet
    if not tools_used and st.session_state.get("enable_web_search", False):
        # Check if query has search intent
        has_search_intent = any(keyword in query_lower for keyword in intent_categories["search"])

        if has_search_intent:
            search_tools = [t for t in available_tools if "search" in t.lower()]
            if search_tools:
                tool_name = search_tools[0]  # Use the first available search tool
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)
                # Update session state immediately for UI feedback
                st.session_state.mcp_tools_used = tools_used.copy()

                # Store the fact that we're using search in session state
                # This will be used by the AI module to ensure search results are incorporated
                st.session_state.mcp_using_search = True

    # Check for complex tasks, equations, or physics problems that would benefit from mcp-reasoner
    has_reasoning_intent = any(keyword in query_lower for keyword in intent_categories["reasoning"])

    if has_reasoning_intent and not any("mcp-reasoner" in tool for tool in tools_used):
        reasoner_tools = [t for t in available_tools if "mcp-reasoner" in t]
        if reasoner_tools:
            # Select the appropriate reasoner function
            if "breakdown" in query_lower or "complex task" in query_lower:
                breakdown_tools = [t for t in reasoner_tools if "breakdown_complex_task" in t]
                if breakdown_tools:
                    tool_name = breakdown_tools[0]
                    status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                    tools_used.append(tool_name)
            elif "equation" in query_lower or "formula" in query_lower:
                equation_tools = [t for t in reasoner_tools if "solve_equations" in t]
                if equation_tools:
                    tool_name = equation_tools[0]
                    status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                    tools_used.append(tool_name)
            else:
                # Default to the first available reasoner tool
                tool_name = reasoner_tools[0]
                status_placeholder.warning(f"🔍 Using tool: {tool_name}")
                tools_used.append(tool_name)

            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Add news-specific tools for news-related queries
    has_news_intent = any(keyword in query_lower for keyword in intent_categories["news"])

    if has_news_intent:
        # First, look for tools specifically designed for news
        news_tools = [t for t in available_tools if "news" in t.lower()]

        # If no specific news tools, use any search tool
        if not news_tools:
            # Get all available search tools
            search_tools = [t for t in available_tools if "search" in t.lower()]

            # Sort search tools to prioritize more comprehensive search tools
            # This avoids hardcoding specific tool names
            prioritized_search_tools = []

            # First add tools that might be good for news (deep research, etc.)
            for tool in search_tools:
                if any(term in tool.lower() for term in ["deep", "research", "comprehensive"]):
                    prioritized_search_tools.append(tool)

            # Then add any remaining search tools
            for tool in search_tools:
                if tool not in prioritized_search_tools:
                    prioritized_search_tools.append(tool)

            news_tools = prioritized_search_tools

        if news_tools and news_tools[0] not in tools_used:
            tool_name = news_tools[0]
            status_placeholder.warning(f"🔍 Using tool for news query: {tool_name}")
            tools_used.append(tool_name)
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

            # Mark that we're using search for news
            st.session_state.mcp_using_search = True

    # Add code-specific tools for code-related queries
    has_documentation_intent = any(keyword in query_lower for keyword in intent_categories["documentation"])

    if has_documentation_intent or "code" in query_lower or "programming" in query_lower:
        code_tools = [t for t in available_tools if "documentation" in t.lower() or "perplexity" in t.lower()]
        if code_tools and code_tools[0] not in tools_used:
            tool_name = code_tools[0]
            status_placeholder.warning(f"🔍 Using tool: {tool_name}")
            tools_used.append(tool_name)
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # Add web-specific tools for web-related queries if not already added
    has_web_intent = any(keyword in query_lower for keyword in intent_categories["web_scraping"] + intent_categories["web_crawling"])

    # Also check for domain names in the query
    domain_in_query = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\b', query_lower) is not None

    # Check for "content from" or similar phrases
    content_from_pattern = re.search(r'(content|information|data|text)\s+from', query_lower)

    # Check for "scrape" specifically
    scrape_in_query = "scrape" in query_lower

    # Combine all web-related indicators
    web_related_query = has_web_intent or domain_in_query or content_from_pattern or scrape_in_query

    if web_related_query and not any(("scrape" in tool or "crawl" in tool or "firecrawl" in tool) for tool in tools_used):
        # Prioritize firecrawl tools
        firecrawl_tools = [t for t in available_tools if "firecrawl" in t.lower()]

        if firecrawl_tools:
            # Prefer scrape over crawl for simple requests
            scrape_tools = [t for t in firecrawl_tools if "scrape" in t.lower()]
            if scrape_tools:
                tool_name = scrape_tools[0]
            else:
                tool_name = firecrawl_tools[0]

            status_placeholder.warning(f"🔍 Using web tool: {tool_name}")
            tools_used.append(tool_name)
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()
        else:
            # Fall back to any web tools
            web_tools = [t for t in available_tools if "scrape" in t.lower() or "crawl" in t.lower()]
            if web_tools:
                tool_name = web_tools[0]
                status_placeholder.warning(f"🔍 Using web tool: {tool_name}")
                tools_used.append(tool_name)
                # Update session state immediately for UI feedback
                st.session_state.mcp_tools_used = tools_used.copy()

    # Add research-specific tools for research-related queries
    has_research_intent = any(keyword in query_lower for keyword in intent_categories["research"])

    if has_research_intent and not any("research" in tool for tool in tools_used):
        research_tools = [t for t in available_tools if "research" in t.lower() or "serper" in t.lower()]
        if research_tools:
            tool_name = research_tools[0]
            status_placeholder.warning(f"🔍 Using tool: {tool_name}")
            tools_used.append(tool_name)
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()

    # If no tools were selected but we have web search enabled, use a search tool as fallback
    if not tools_used and st.session_state.get("enable_web_search", False):
        # Check if this is a news-related query
        has_news_intent = any(keyword in query_lower for keyword in intent_categories["news"])

        # Get all available search tools
        search_tools = [t for t in available_tools if "search" in t.lower()]

        if search_tools:
            # For news queries, prioritize tools that might be better for news
            if has_news_intent:
                # Sort search tools to prioritize more comprehensive search tools
                prioritized_search_tools = []

                # First add tools that might be good for news (deep research, etc.)
                for tool in search_tools:
                    if any(term in tool.lower() for term in ["deep", "research", "comprehensive"]):
                        prioritized_search_tools.append(tool)

                # Then add any remaining search tools
                for tool in search_tools:
                    if tool not in prioritized_search_tools:
                        prioritized_search_tools.append(tool)

                search_tools = prioritized_search_tools

            tool_name = search_tools[0]
            status_placeholder.warning(f"🔍 Using {'news ' if has_news_intent else ''}search tool: {tool_name}")
            tools_used.append(tool_name)
            # Update session state immediately for UI feedback
            st.session_state.mcp_tools_used = tools_used.copy()
            st.session_state.mcp_using_search = True

    # If still no tools were selected, notify the user
    if not tools_used:
        status_placeholder.warning("No specific MCP tools were selected for this query.")
        time.sleep(1.5)
    else:
        # Show completion message if tools were used
        status_placeholder.success(f"✅ Selected {len(tools_used)} tool(s), generating response...")
        time.sleep(0.5)

    # Don't clear the status message here - it will be cleared by app.py after processing is complete

    return tools_used
