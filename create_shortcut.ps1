# PowerShell script to create Windows Start Menu shortcuts for Grok Chat

# Get the current directory where the script is running
$currentDir = (Get-Item -Path ".\").FullName

# Define paths
$launchBatchPath = Join-Path -Path $currentDir -ChildPath "launch_grok_chat.bat"
$setupBatchPath = Join-Path -Path $currentDir -ChildPath "setup_environment.bat"
$iconPath = Join-Path -Path $currentDir -ChildPath "favicon.ico"
$startMenuPath = [System.Environment]::GetFolderPath('StartMenu')
$programsPath = Join-Path -Path $startMenuPath -ChildPath "Programs"

# Create Grok Chat folder in Start Menu
$grokChatFolder = Join-Path -Path $programsPath -ChildPath "Grok Chat"
if (-not (Test-Path $grokChatFolder)) {
    New-Item -Path $grokChatFolder -ItemType Directory | Out-Null
}

# Create the main application shortcut
$appShortcutPath = Join-Path -Path $grokChatFolder -ChildPath "Grok Chat.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($appShortcutPath)
$Shortcut.TargetPath = $launchBatchPath
$Shortcut.WorkingDirectory = $currentDir
$Shortcut.Description = "Grok Chat Interface - Streamlit-based chat application for xAI's Grok models"

# Set the icon if it exists
if (Test-Path $iconPath) {
    $Shortcut.IconLocation = "$iconPath,0"
}

# Save the shortcut
$Shortcut.Save()

# Create the environment setup shortcut
$setupShortcutPath = Join-Path -Path $grokChatFolder -ChildPath "Setup Environment.lnk"
$SetupShortcut = $WshShell.CreateShortcut($setupShortcutPath)
$SetupShortcut.TargetPath = $setupBatchPath
$SetupShortcut.WorkingDirectory = $currentDir
$SetupShortcut.Description = "Set up environment variables for Grok Chat"

# Set the icon if it exists
if (Test-Path $iconPath) {
    $SetupShortcut.IconLocation = "$iconPath,0"
}

# Save the shortcut
$SetupShortcut.Save()

Write-Host "Shortcuts created successfully in: $grokChatFolder"
Write-Host "You can now find 'Grok Chat' folder in your Start Menu with the following shortcuts:"
Write-Host "- Grok Chat: Launches the application"
Write-Host "- Setup Environment: Configures your API keys"
