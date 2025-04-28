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

    # When MCP is enabled, we'll use the actual MCP tools
    # For now, we're just tracking which tools are being used
    if use_mcp:
        # In a real implementation, this would be populated by the actual MCP framework
        # For now, we'll just track that we're using search functionality
        if "search_brave-search" not in st.session_state.mcp_tools_used:
            st.session_state.mcp_tools_used.append("search_brave-search")

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

Your primary goal is to provide helpful, ACCURATE information that directly addresses what the user is asking.
"""

    # Initialize context and search metadata
    context = ""
    search_metadata = {}

    # Fetch search results if enabled or if MCP is enabled (since MCP uses search tools)
    if use_search or use_mcp:
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
        if use_mcp and st.session_state.mcp_tools_used:
            mcp_tools_info = "\n\nMCP tools used for this query:\n" + "\n".join([f"- {tool}" for tool in st.session_state.mcp_tools_used])

        prompt = f"""Query: "{user_message}"
Today's date is {current_date}.

SEARCH RESULTS (YOU MUST USE THESE TO ANSWER THE QUERY):
{context}{mcp_tools_info}

CRITICAL INSTRUCTIONS:
1. You MUST use the search results above to answer the query
2. You MUST cite sources using [1], [2], etc. for ANY factual information
3. You MUST include a "References" section at the end listing all sources
4. If search results don't provide enough information, clearly state this
5. NEVER present information as factual without citing a source
6. If MCP tools were used, you MUST incorporate their results in your answer
7. DO NOT claim you don't have access to current information if search results are provided

Be direct and concise in your answer.
"""
    else:
        # Use standard prompt without search context but still include date awareness
        mcp_tools_info = ""
        if use_mcp and st.session_state.mcp_tools_used:
            mcp_tools_info = "\n\nMCP tools used for this query:\n" + "\n".join([f"- {tool}" for tool in st.session_state.mcp_tools_used])

        prompt = f"""Today's date is {current_date}.

Answer directly: {user_message}{mcp_tools_info}

IMPORTANT: If you don't have enough information to answer factually, clearly state this. DO NOT make up information or present speculative information as fact.
If MCP tools were used, make sure to incorporate their results in your answer."""

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
            "content": f"Sorry, I encountered an error while processing your request: {str(e)}",
            "reasoning": "",
            "mcp_tools_used": []
        }
