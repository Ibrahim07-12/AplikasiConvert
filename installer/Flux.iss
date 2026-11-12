#define AppName "Flux"
#define AppVersion "1.0.0"
#define AppPublisher "Flux"
#define AppExeName "Flux.exe"

[Setup]
AppId={{B1A2E3F4-9D8B-4A5C-9C3A-FLUX2026}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Flux
DefaultGroupName=Flux
OutputDir=installer-output
OutputBaseFilename=Flux-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "..\dist\Flux\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autodesktop}\Flux"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Flux"; Filename: "{app}\{#AppExeName}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Flux"; Flags: nowait postinstall skipifsilent
