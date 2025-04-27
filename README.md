# Grok Chat Interface

A Streamlit-based chat application that provides a user-friendly interface for interacting with xAI's Grok models.

## Features

- **Interactive Chat Interface**: Clean and intuitive UI for conversing with Grok models
- **Conversation Management**: Save, rename, and delete conversations
- **Enhanced Web Search Integration**: Advanced Brave Search integration with intelligent query processing, result clustering, and source attribution
- **Customizable Settings**:
  - Adjustable reasoning effort (Low, Medium, High)
  - Option to view the model's reasoning process
  - Automatic model selection from available xAI models via dropdown
- **LaTeX Support**: Proper rendering of mathematical expressions and equations
- **Copy Functionality**: Easy copying of assistant responses via expandable sections

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Note: Make sure all dependencies are properly installed before running the application.

## Environment Setup

Set the following environment variables:

- `XAI_API_KEY`: Your xAI API key for accessing Grok models
- `BRAVE_API_KEY`: Your Brave Search API key (optional, for web search functionality)

## Usage

Run the application with:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501` by default.

### Troubleshooting

If you encounter any errors when running the application:

1. Make sure all dependencies are installed correctly:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify that your environment variables are set correctly.

## Configuration

The application stores settings in `settings.json` and conversations in `conversations.json`. These files are automatically created and managed by the application.

## Requirements

- Python 3.7+
- Streamlit
- OpenAI Python client
- Requests

All dependencies are listed in the `requirements.txt` file.

### Copy Functionality

The application uses Streamlit's built-in components to provide copy functionality:
- Each assistant response includes an expandable "Copy this response" section
- When expanded, the response is displayed in a code block with a built-in copy button
- This approach ensures reliable copying across different environments and browsers

## License

MIT

## Acknowledgements

- xAI for providing the Grok models
- Brave Search for web search capabilities
- Streamlit for the web application framework
- Augment for AI code assistance
