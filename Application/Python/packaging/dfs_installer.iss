; Inno Setup definition for the DFS per-user Windows installer.
; build_installer.py supplies all three preprocessor values.

#ifndef MyAppVersion
  #error MyAppVersion must be defined by the release builder.
#endif
#ifndef MySourceDir
  #error MySourceDir must be defined by the release builder.
#endif
#ifndef MyOutputDir
  #error MyOutputDir must be defined by the release builder.
#endif

#define MyAppName "Dee's Fighting Ships"
#define MyAppExeName "DFS.exe"
#define MyAppId "{{818A90AB-06B1-5E53-B3AD-0C90EDF0AB8E}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=DFS Project
DefaultDirName={localappdata}\Programs\Dee's Fighting Ships
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#MyOutputDir}
OutputBaseFilename=Dees-Fighting-Ships-{#MyAppVersion}-Windows-x64-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
