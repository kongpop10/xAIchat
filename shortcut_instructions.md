# Adding Grok Chat to Windows Start Menu

This guide explains how to add Grok Chat shortcuts to your Windows Start Menu for easy access.

## Prerequisites

- Make sure you have all the required dependencies installed:
  ```
  pip install -r requirements.txt
  ```

## Installation Steps

1. **Run the PowerShell script as Administrator**:
   - Right-click on `create_shortcut.ps1`
   - Select "Run with PowerShell"
   - If prompted about execution policy, you may need to run:
     ```powershell
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     ```
   - Then run the script again

2. **Verify Installation**:
   - Check your Start Menu for a new "Grok Chat" folder
   - Inside you should find two shortcuts:
     - **Grok Chat**: Launches the main application
     - **Setup Environment**: Helps you configure your API keys

3. **Set Up Environment Variables**:
   - Run the "Setup Environment" shortcut first
   - Enter your xAI API key when prompted
   - Optionally enter your Brave Search API key if you have one

4. **Using the Application**:
   - Click on the "Grok Chat" shortcut in the Start Menu
   - The application will launch in your default web browser at http://localhost:8501

## What Gets Installed

The installation creates:
- A "Grok Chat" folder in your Start Menu
- Two shortcuts inside this folder:
  1. **Grok Chat**: Launches the Streamlit application
  2. **Setup Environment**: Configures your API keys

## Troubleshooting

If you encounter any issues:

1. **Shortcuts don't appear**:
   - Make sure you ran the PowerShell script as administrator
   - Check if the Start Menu folder was created at: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Grok Chat`

2. **Application doesn't start**:
   - Make sure Streamlit is installed: `pip install streamlit`
   - Verify that all dependencies are installed: `pip install -r requirements.txt`
   - Check that your xAI API key is set correctly using the "Setup Environment" shortcut

3. **Environment variables not working**:
   - Run the "Setup Environment" shortcut as administrator for system-wide settings
   - Restart your computer after setting environment variables
   - Verify the variables are set by running `echo %XAI_API_KEY%` in Command Prompt

4. **Icon doesn't appear**:
   - Verify that the favicon.ico file exists in the application directory
   - You can manually set the icon by right-clicking the shortcut, selecting Properties, and clicking "Change Icon"

## Manual Installation

If the script doesn't work, you can manually create shortcuts:

1. Right-click on your desktop or in the Start Menu folder
2. Select New > Shortcut
3. Browse to the location of `launch_grok_chat.bat` or `setup_environment.bat` and select it
4. Click Next and give the shortcut a name (e.g., "Grok Chat" or "Setup Environment")
5. Right-click the new shortcut and select Properties
6. Click "Change Icon" and browse to the favicon.ico file
7. Click OK to save the changes

## Uninstallation

To remove the shortcuts:
1. Navigate to: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\`
2. Delete the "Grok Chat" folder

This will only remove the shortcuts, not the application itself.
