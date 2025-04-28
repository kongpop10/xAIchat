"""
Conversation module for the Grok Chat application.
Handles conversation management, loading, and saving.
"""
import json
from datetime import datetime

def load_conversations():
    """
    Load conversations from the conversations.json file.
    
    Returns:
        dict: Conversations data or empty dict if file doesn't exist or has errors
    """
    try:
        with open("conversations.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_conversation(conversations, conversation_id, messages, title):
    """
    Save a conversation to the conversations dictionary and file.
    
    Args:
        conversations (dict): Dictionary of all conversations
        conversation_id (str): ID of the conversation to save
        messages (list): List of message objects in the conversation
        title (str): Title of the conversation
    """
    conversations[conversation_id] = {
        "messages": messages,
        "title": title,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("conversations.json", "w") as f:
        json.dump(conversations, f)

def get_default_system_message():
    """
    Get the default system message for new conversations.
    
    Returns:
        dict: Default system message
    """
    return {
        "role": "system", 
        "content": "You are a highly intelligent AI assistant powered by the Grok model from xAI."
    }

def create_new_conversation(conversations, conversation_id, title="New Conversation"):
    """
    Create a new conversation with default system message.
    
    Args:
        conversations (dict): Dictionary of all conversations
        conversation_id (str): ID for the new conversation
        title (str, optional): Title for the new conversation. Defaults to "New Conversation".
        
    Returns:
        list: Initial messages list for the new conversation
    """
    messages = [get_default_system_message()]
    
    # Save the new conversation
    save_conversation(conversations, conversation_id, messages, title)
    
    return messages
