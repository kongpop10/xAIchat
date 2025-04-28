"""
Configuration module for the Grok Chat application.
Handles loading and saving settings, MCP settings, and default configurations.
"""
import os
import json

# Constants
SETTINGS_FILE = "settings.json"
MCP_SETTINGS_FILE = "mcp_settings.json"

def load_settings():
    """
    Load application settings from the settings file.
    
    Returns:
        dict: Application settings or empty dict if file doesn't exist or has errors
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(settings):
    """
    Save application settings to the settings file.
    
    Args:
        settings (dict): Application settings to save
    """
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)
    except Exception:
        pass

def load_mcp_settings():
    """
    Load MCP settings from the MCP settings file.
    First tries to load from @mcp_settings.json (user's private file),
    then falls back to regular mcp_settings.json if needed.
    
    Returns:
        dict: MCP settings or empty dict if no files exist or have errors
    """
    error_messages = []

    # First try to load from @mcp_settings.json (user's private file)
    if os.path.exists("@" + MCP_SETTINGS_FILE):
        try:
            with open("@" + MCP_SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            error_messages.append(f"Error loading @{MCP_SETTINGS_FILE}: {str(e)}")
            # Fall back to regular mcp_settings.json

    # If @mcp_settings.json doesn't exist or had an error, try regular mcp_settings.json
    if os.path.exists(MCP_SETTINGS_FILE):
        try:
            with open(MCP_SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            error_messages.append(f"Error loading {MCP_SETTINGS_FILE}: {str(e)}")
            return {}

    # If no settings file exists, return empty settings
    return {}

def save_mcp_settings(mcp_settings):
    """
    Save MCP settings to the MCP settings file.
    First tries to save to @mcp_settings.json if it exists,
    then falls back to regular mcp_settings.json if needed.
    
    Args:
        mcp_settings (dict): MCP settings to save
    """
    error_messages = []

    # First try to save to @mcp_settings.json if it exists
    if os.path.exists("@" + MCP_SETTINGS_FILE):
        try:
            with open("@" + MCP_SETTINGS_FILE, "w") as f:
                json.dump(mcp_settings, f, indent=2)
            return
        except Exception as e:
            error_messages.append(f"Error saving to @{MCP_SETTINGS_FILE}: {str(e)}")
            # Fall back to regular mcp_settings.json

    # If @mcp_settings.json doesn't exist or had an error, save to regular mcp_settings.json
    try:
        with open(MCP_SETTINGS_FILE, "w") as f:
            json.dump(mcp_settings, f, indent=2)
    except Exception as e:
        error_messages.append(f"Error saving MCP settings: {str(e)}")

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
        # Success message will be shown after page config
    except Exception:
        # Error message will be shown after page config
        pass

    return default_settings

# Default settings
DEFAULT_SETTINGS = {
    "reasoning_effort": "medium",
    "show_reasoning": False,
    "model_name": "grok-3-mini-beta",
    "enable_web_search": True,
    "enable_mcp": False
}

# MCP server descriptions
MCP_SERVER_DESCRIPTIONS = {
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
