import base64
from pathlib import Path

def get_base64_encoded_image(image_path):
    """Get base64 encoded image data for use as a favicon."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def img_to_bytes(img_path):
    """Convert image to bytes for embedding in HTML."""
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

def get_xai_icon_html():
    """Return HTML for the xAI logo as an SVG."""
    # This is a more accurate version of the xAI logo
    icon_html = """
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 512 362" fill="none">
        <rect width="512" height="362" fill="white"/>
        <path d="M256 50 L462 312 L50 312 Z" fill="black"/>
        <!-- Add the "x" text in the center of the triangle -->
        <text x="256" y="220" font-family="Arial, sans-serif" font-size="120" font-weight="bold" fill="white" text-anchor="middle">x</text>
    </svg>
    """
    b64 = base64.b64encode(icon_html.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"

def get_grok_icon_html():
    """Return HTML for a custom Grok icon."""
    icon_html = """
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#00BFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 16v-4"/>
        <path d="M12 8h.01"/>
        <path d="M9 12h6"/>
        <path d="M8 5.2A11 11 0 0 1 12 4"/>
        <path d="M16.8 8A11 11 0 0 1 19 12"/>
        <path d="M16 19.8A11 11 0 0 1 12 21"/>
        <path d="M7.2 16A11 11 0 0 1 5 12"/>
    </svg>
    """
    b64 = base64.b64encode(icon_html.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"
