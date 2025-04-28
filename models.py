"""
Models module for the Grok Chat application.
Handles xAI model integration and API interactions.
"""
import os
from functools import lru_cache
from openai import OpenAI

@lru_cache(maxsize=1)
def fetch_xai_models():
    """
    Fetch available models from xAI API and cache the results.
    
    Returns:
        tuple: (list of model IDs, error message or None)
    """
    error_message = None
    try:
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            error_message = "xAI API key not set. Please set XAI_API_KEY in your environment."
            return ["grok-3-mini-beta", "grok-3-mini-fast-beta"], error_message  # Default models

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

        return models, None
    except Exception as e:
        error_message = f"Error fetching models: {str(e)}"
        return ["grok-3-mini-beta", "grok-3-mini-fast-beta"], error_message  # Default models as fallback

def create_openai_client():
    """
    Create and return an OpenAI client configured for xAI.
    
    Returns:
        OpenAI: Configured OpenAI client or None if API key is not set
    """
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        return None
        
    return OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )

# Constants for model interaction
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
