# 🚀 Grok Chat Interface

A Streamlit-based chat application that provides a user-friendly interface for interacting with xAI's Grok models, featuring web search integration and Model Context Protocol (MCP) support.

## 💡 Features

- 💬 **Interactive Chat Interface**: Clean and intuitive UI for conversing with Grok models
- 📚 **Conversation Management**: Save, rename, and delete conversations
- 🌐 **Enhanced Web Search Integration**:
  - Advanced Brave Search integration with intelligent query processing
  - Automatic result clustering and source attribution
  - Freshness filtering for time-sensitive queries
  - References section with citations in responses
- ⚙️ **Customizable Settings**:
  - Adjustable reasoning effort (Low, Medium, High)
  - Option to view the model's reasoning process
  - Dynamic model selection from available xAI models via API
- 🔌 **Model Context Protocol (MCP) Support**:
  - Configure and use MCP to enhance AI capabilities with external tools
  - Transparent tool usage indicators in responses
  - Support for multiple MCP servers including Brave Search, Perplexity, Tavily, and more
- ➗ **LaTeX Support**: Proper rendering of mathematical expressions and equations
- 📋 **Copy Functionality**: Easy copying of assistant responses via expandable sections
- 🎨 **Official xAI Branding**: Uses the official xAI icon from x.ai/api

## 🔧 Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Note: Make sure all dependencies are properly installed before running the application.

## ⚙️ Environment Setup

Set the following environment variables:

- `XAI_API_KEY`: Your xAI API key for accessing Grok models
- `BRAVE_API_KEY`: Your Brave Search API key (optional, for web search functionality)

## 💻 Usage

Run the application with:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501` by default.

### ⚠️ Troubleshooting

If you encounter any errors when running the application:

1. Make sure all dependencies are installed correctly:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify that your environment variables are set correctly.

3. Check that your xAI API key has access to the models you're trying to use.

## ⚙️ Configuration

The application stores settings in `settings.json` and conversations in `conversations.json`. These files are automatically created and managed by the application.

### MCP Configuration

The application supports Model Context Protocol (MCP) for enhanced AI capabilities:

1. Enable MCP using the toggle in the sidebar
2. Configure MCP settings by clicking on the "MCP Settings" expander
3. Edit the JSON configuration to match your MCP server setup
4. Save the configuration to apply changes

The MCP settings are stored in `mcp_settings.json` in the same format as Claude's MCP configuration. For security reasons, this file is excluded from version control as it may contain API keys.

### Web Search Integration

The application integrates with Brave Search to provide more informed responses:

1. Enable Web Search using the toggle in the sidebar
2. The AI will automatically determine when to use search based on your query
3. Search results are processed and incorporated into the response
4. A references section is added to responses with citations to the sources used

## ✅ Requirements

- Python 3.7+
- Streamlit
- OpenAI Python client
- Requests

All dependencies are listed in the `requirements.txt` file.

### 📋 Copy Functionality

The application uses Streamlit's built-in components to provide copy functionality:
- Each assistant response includes an expandable "Copy this response" section
- When expanded, the response is displayed in a code block with a built-in copy button
- This approach ensures reliable copying across different environments and browsers

## 📜 License

MIT

## 👏 Acknowledgements

- xAI for providing the Grok models and API
- Brave Search for web search capabilities
- Streamlit for the web application framework
- Model Context Protocol (MCP) for enhanced AI capabilities
- Augment for AI code assistance
