"""
AI module for the Grok Chat application.
Handles AI response generation and integration with search and MCP.
"""
import streamlit as st
from datetime import datetime
from models import create_openai_client, LLM_MATH_FORMATTING_INSTRUCTION
from search import brave_search, format_search_results_for_context

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

    # When MCP is enabled, get available tools from MCP settings
    if use_mcp:
        # Import here to avoid circular imports
        from mcp import select_mcp_tools, execute_mcp_tool, get_mcp_system_instructions

        # Get MCP system instructions for the AI

        # Select appropriate tools based on query content
        # This will populate st.session_state.mcp_tools_used
        selected_tools = select_mcp_tools(user_message)

        # Store tool results
        tool_results = []

        # Execute each selected tool
        for tool_name in selected_tools:
            result = execute_mcp_tool(tool_name, user_message)
            if result["success"]:
                tool_results.append(result)

        # Store tool results in session state
        st.session_state.mcp_tool_results = tool_results

    # Get current date for AI awareness
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Define the base system prompt for Grok with date awareness and emphasis on factual accuracy
    grok_system_prompt = f"""You are an AI assistant powered by the Grok model from xAI. Today's date is {current_date}.

CRITICAL INSTRUCTIONS:
1. Be direct and concise - focus on answering the user's question
2. NEVER present speculative information as fact
3. When using search results or external tools, you MUST cite your sources
4. Always include a "References" section when providing factual information
5. If search results are provided, you MUST use them to answer the query
6. DO NOT claim you don't have access to current information if search results are provided
7. When using MCP tools, always incorporate their results in your answer
8. For news-related queries, prioritize the most recent information and clearly state the date of the information

Your primary goal is to provide helpful, ACCURATE information that directly addresses what the user is asking.
"""

    # Add special handling for news queries
    if hasattr(st.session_state, 'is_news_query') and st.session_state.is_news_query:
        grok_system_prompt += """
SPECIAL INSTRUCTIONS FOR NEWS QUERIES:
1. Focus on providing the most recent information available in the search results
2. Clearly state the publication date of news articles when available
3. Organize information chronologically when possible, with newest information first
4. Highlight breaking or developing news stories
5. Provide a balanced overview of the topic from multiple sources
6. Avoid speculation about future developments unless explicitly cited from sources
"""

    # Add MCP system instructions if MCP is enabled
    if use_mcp:
        # Get MCP system instructions
        mcp_instructions = get_mcp_system_instructions()
        grok_system_prompt += mcp_instructions

        # Add instruction to separate tool reasoning from main response
        grok_system_prompt += "\n\nIMPORTANT: When using MCP tools, DO NOT incorporate the tool reasoning directly into your main response text. Instead, place tool results in a separate section at the end of your response."

        # Add specific instructions for web scraping
        grok_system_prompt += "\n\nWhen web scraping tools are used, you MUST include the content from the scraped website in your response. Format the scraped content clearly and include the source URL. For example: 'According to [website], [content from website]...'"

    # Initialize context and search metadata
    context = ""
    search_metadata = {}

    # Check if we should use Brave Search - respect the web search toggle
    use_brave_search = use_search

    # Only use Brave Search with MCP if it's not disabled in MCP settings and web search is enabled
    if use_mcp:
        # Check if Brave Search is available in MCP tools
        brave_search_available = False
        for tool in st.session_state.mcp_tools_used:
            if "search_brave-search" in tool:
                brave_search_available = True
                break

        # If Brave Search is not available in MCP tools or web search is disabled, don't use it
        if not brave_search_available or not use_search:
            use_brave_search = False

    # Fetch search results if enabled and Brave Search is available
    if use_brave_search:
        try:
            # Determine optimal search parameters based on query complexity
            query_length = len(user_message.split())
            result_count = min(10, max(5, query_length // 3))  # Scale results with query complexity

            # Get freshness parameter based on query content
            time_sensitive_keywords = ["news", "recent", "latest", "today", "current", "breaking", "update", "development"]
            is_news_query = any(keyword in user_message.lower() for keyword in time_sensitive_keywords)

            # Use day freshness for news queries, and add special handling for news
            freshness = "d" if is_news_query else None

            # For news queries, add a note to session state to ensure proper handling
            if is_news_query:
                st.session_state.is_news_query = True

            # Perform the search with enhanced parameters
            search_results = brave_search(
                query=user_message,
                count=result_count,
                freshness=freshness
            )

            # Format search results for context
            if search_results:
                context, search_metadata = format_search_results_for_context(search_results, user_message)
                # Add search results to session state for tracking (without UI notification)
                if use_mcp and "search_results_count" not in st.session_state:
                    st.session_state.search_results_count = len(search_results)
            else:
                # Track that no search results were found (without UI notification)
                if use_mcp:
                    st.session_state.search_results_count = 0

        except Exception as e:
            st.warning(f"Search error: {str(e)}. Proceeding without search results.")

    # Construct the prompt with context if available
    if context:
        # Create a structured prompt with search results - more direct and emphasizing citations
        mcp_tools_info = ""
        mcp_tool_results_info = ""

        if use_mcp and st.session_state.mcp_tools_used:
            mcp_tools_info = "\n\nMCP tools used for this query:\n" + "\n".join([f"- {tool}" for tool in st.session_state.mcp_tools_used])

            # Add tool results if available
            if hasattr(st.session_state, 'mcp_tool_results') and st.session_state.mcp_tool_results:
                mcp_tool_results_info = "\n\nTOOL RESULTS:\n"
                for result in st.session_state.mcp_tool_results:
                    mcp_tool_results_info += f"Tool: {result['tool']}\n"
                    if isinstance(result['data'], list):
                        # Format search results
                        for i, item in enumerate(result['data']):
                            if isinstance(item, dict) and 'title' in item and 'url' in item:
                                mcp_tool_results_info += f"[{i+1}] {item.get('title', 'No title')} - {item.get('url', 'No URL')}\n"
                                if 'description' in item:
                                    mcp_tool_results_info += f"    {item['description']}\n"
                    elif isinstance(result['data'], dict) and 'success' in result['data'] and result['data']['success']:
                        # Format web scraping results
                        if 'url' in result['data'] and 'title' in result['data'] and 'content' in result['data']:
                            # Single page scrape result
                            mcp_tool_results_info += f"Scraped content from: {result['data']['title']} ({result['data']['url']})\n\n"

                            # Truncate content if too long
                            content = result['data']['content']
                            if len(content) > 2000:
                                content = content[:2000] + "... [Content truncated]"

                            mcp_tool_results_info += f"{content}\n"

                            # Add links if available
                            if 'links' in result['data'] and result['data']['links']:
                                mcp_tool_results_info += "\nLinks from the page:\n"
                                for i, link in enumerate(result['data']['links'][:5]):
                                    mcp_tool_results_info += f"- {link.get('text', 'Link')} ({link.get('url', '')})\n"

                        elif 'pages' in result['data'] and result['data']['pages']:
                            # Multi-page crawl result
                            mcp_tool_results_info += f"Crawled content from: {result['data']['base_url']}\n"
                            mcp_tool_results_info += f"Pages crawled: {len(result['data']['pages'])}\n\n"

                            # Add content from each page (limited)
                            for i, page in enumerate(result['data']['pages'][:3]):
                                mcp_tool_results_info += f"Page {i+1}: {page.get('title', 'No title')} ({page.get('url', 'No URL')})\n"

                                # Truncate content if too long
                                content = page.get('content', '')
                                if len(content) > 1000:
                                    content = content[:1000] + "... [Content truncated]"

                                mcp_tool_results_info += f"{content}\n\n"
                    else:
                        # Format other results
                        mcp_tool_results_info += f"Result: {result['data']}\n"
                    mcp_tool_results_info += "\n"

        # Check if this is a news-related query
        is_news_query = hasattr(st.session_state, 'is_news_query') and st.session_state.is_news_query

        # Add special instructions for news queries
        news_instructions = """
10. For news queries, prioritize the most recent information and clearly state the publication date
11. Organize news information chronologically when possible, with newest information first
12. Highlight breaking or developing news stories
""" if is_news_query else ""

        prompt = f"""Query: "{user_message}"
Today's date is {current_date}.

SEARCH RESULTS (YOU MUST USE THESE TO ANSWER THE QUERY):
{context}{mcp_tools_info}{mcp_tool_results_info}

CRITICAL INSTRUCTIONS:
1. You MUST use the search results and tool results above to answer the query
2. You MUST cite sources using [1], [2], etc. for ANY factual information
3. You MUST include a "References" section at the end listing all sources
4. If search results don't provide enough information, clearly state this
5. NEVER present information as factual without citing a source
6. If MCP tools were used, incorporate their results in your answer BUT DO NOT mention the tools by name in your response
7. DO NOT claim you don't have access to current information if search results are provided
8. DO NOT include any text about which tools were used in your response - this will be shown separately
9. If web scraping results are provided, you MUST include the content from the scraped website in your answer and cite the source{news_instructions}

Be direct and concise in your answer.
"""
    else:
        # Use standard prompt without search context but still include date awareness
        mcp_tools_info = ""
        mcp_tool_results_info = ""

        if use_mcp and st.session_state.mcp_tools_used:
            mcp_tools_info = "\n\nMCP tools used for this query:\n" + "\n".join([f"- {tool}" for tool in st.session_state.mcp_tools_used])

            # Add tool results if available
            if hasattr(st.session_state, 'mcp_tool_results') and st.session_state.mcp_tool_results:
                mcp_tool_results_info = "\n\nTOOL RESULTS:\n"
                for result in st.session_state.mcp_tool_results:
                    mcp_tool_results_info += f"Tool: {result['tool']}\n"
                    if isinstance(result['data'], list):
                        # Format search results
                        for i, item in enumerate(result['data']):
                            if isinstance(item, dict) and 'title' in item and 'url' in item:
                                mcp_tool_results_info += f"[{i+1}] {item.get('title', 'No title')} - {item.get('url', 'No URL')}\n"
                                if 'description' in item:
                                    mcp_tool_results_info += f"    {item['description']}\n"
                    elif isinstance(result['data'], dict) and 'success' in result['data'] and result['data']['success']:
                        # Format web scraping results
                        if 'url' in result['data'] and 'title' in result['data'] and 'content' in result['data']:
                            # Single page scrape result
                            mcp_tool_results_info += f"Scraped content from: {result['data']['title']} ({result['data']['url']})\n\n"

                            # Truncate content if too long
                            content = result['data']['content']
                            if len(content) > 2000:
                                content = content[:2000] + "... [Content truncated]"

                            mcp_tool_results_info += f"{content}\n"

                            # Add links if available
                            if 'links' in result['data'] and result['data']['links']:
                                mcp_tool_results_info += "\nLinks from the page:\n"
                                for i, link in enumerate(result['data']['links'][:5]):
                                    mcp_tool_results_info += f"- {link.get('text', 'Link')} ({link.get('url', '')})\n"

                        elif 'pages' in result['data'] and result['data']['pages']:
                            # Multi-page crawl result
                            mcp_tool_results_info += f"Crawled content from: {result['data']['base_url']}\n"
                            mcp_tool_results_info += f"Pages crawled: {len(result['data']['pages'])}\n\n"

                            # Add content from each page (limited)
                            for i, page in enumerate(result['data']['pages'][:3]):
                                mcp_tool_results_info += f"Page {i+1}: {page.get('title', 'No title')} ({page.get('url', 'No URL')})\n"

                                # Truncate content if too long
                                content = page.get('content', '')
                                if len(content) > 1000:
                                    content = content[:1000] + "... [Content truncated]"

                                mcp_tool_results_info += f"{content}\n\n"
                    else:
                        # Format other results
                        mcp_tool_results_info += f"Result: {result['data']}\n"
                    mcp_tool_results_info += "\n"

        # Check if this is a news-related query
        is_news_query = hasattr(st.session_state, 'is_news_query') and st.session_state.is_news_query

        # Add special instructions for news queries
        news_instructions = """
5. For news-related queries, prioritize the most recent information and clearly state the publication date.
6. Organize news information chronologically when possible, with newest information first.
7. Highlight breaking or developing news stories.
""" if is_news_query else ""

        prompt = f"""Today's date is {current_date}.

Answer directly: {user_message}{mcp_tools_info}{mcp_tool_results_info}

IMPORTANT:
1. If you don't have enough information to answer factually, clearly state this. DO NOT make up information or present speculative information as fact.
2. If MCP tools were used, incorporate their results in your answer BUT DO NOT mention the tools by name in your response.
3. DO NOT include any text about which tools were used in your response - this will be shown separately.
4. If web scraping results are provided, you MUST include the content from the scraped website in your answer and cite the source.{news_instructions}"""

    # Add math formatting instructions
    prompt = f"{LLM_MATH_FORMATTING_INSTRUCTION}\n\n{prompt}"

    try:
        # Initialize the OpenAI client with xAI's base URL
        client = create_openai_client()
        if not client:
            return {
                "content": "Error: xAI API key not set. Please set XAI_API_KEY in your environment.",
                "reasoning": "",
                "mcp_tools_used": []
            }

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

            # We'll no longer add the search attribution footer to keep the response clean
            # The search tool usage will be shown in the MCP Tools Used section

        # Clean up the response to remove any tool-related content
        if use_mcp and st.session_state.mcp_tools_used:
            # Remove any lines that mention tools
            content_lines = content.split('\n')
            cleaned_lines = []

            # Skip lines that mention tools or tool usage
            tool_keywords = ['tool', 'mcp', 'search', 'tavily', 'brave', 'perplexity', 'serper', 'firecrawl']
            for line in content_lines:
                # Skip lines that mention tools
                if any(keyword in line.lower() for keyword in tool_keywords) and any(word in line.lower() for word in ['used', 'using', 'utilized', 'provided by', 'powered by', 'via']):
                    continue
                cleaned_lines.append(line)

            # Reassemble the content
            content = '\n'.join(cleaned_lines)

            # Add a note for MCP reasoner if used
            if "mcp-reasoner" in " ".join(st.session_state.mcp_tools_used):
                # Add a note to ensure tool reasoning is separated from main content
                content += "\n\n---\n*Note: Reasoning is provided in this separate section and should not be incorporated into the main response text.*"

        # Reset MCP processing status
        st.session_state.mcp_processing = False

        # Reset news query flag if it exists
        if hasattr(st.session_state, 'is_news_query'):
            del st.session_state.is_news_query

        return {
            "content": content,
            "reasoning": reasoning,
            "mcp_tools_used": st.session_state.mcp_tools_used if use_mcp else []
        }
    except Exception as e:
        # Reset MCP processing status on error
        st.session_state.mcp_processing = False

        # Reset news query flag if it exists
        if hasattr(st.session_state, 'is_news_query'):
            del st.session_state.is_news_query
        st.error(f"Error generating response: {str(e)}")
        return {
            "content": f"Sorry, I encountered an error while processing your request: {str(e)}",
            "reasoning": "",
            "mcp_tools_used": []
        }
