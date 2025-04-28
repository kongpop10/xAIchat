"""
Search module for the Grok Chat application.
Handles Brave Search API integration and search result processing.
"""
import os
import requests
import streamlit as st
import time

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

def format_search_results_for_context(search_results, query):
    """
    Format search results into a context string for the AI.
    
    Args:
        search_results (list): List of search result dictionaries
        query (str): The original search query
        
    Returns:
        tuple: (context_string, search_metadata)
    """
    if not search_results:
        return "", {}
    
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
        "query": query
    }
    
    return context, search_metadata
