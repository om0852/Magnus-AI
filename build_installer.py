import os
import sys

def create_inno_setup_script():
    iss_content = """
[Setup]
AppName=Magnas AI Workstation
AppVersion=1.0
DefaultDirName={autopf}\\MagnasAI
DefaultGroupName=Magnas AI
OutputBaseFilename=MagnasAI_v1.0_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\\MagnasAI\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\Magnas AI"; Filename: "{app}\\MagnasAI.exe"
Name: "{commondesktop}\\Magnas AI"; Filename: "{app}\\MagnasAI.exe"

[Run]
Filename: "{app}\\MagnasAI.exe"; Description: "Launch Magnas AI Workstation"; Flags: nowait postinstall skipifsilent
"""
    iss_path = "MagnasAI_Setup.iss"
    with open(iss_path, "w", encoding="utf-8") as f:
        f.write(iss_content.strip())
    print(f"[Installer Spec] Generated InnoSetup installer script: '{iss_path}'")

if __name__ == "__main__":
    create_inno_setup_script()
