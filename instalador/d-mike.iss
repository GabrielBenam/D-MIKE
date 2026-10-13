; Instalador de D-MIKE (Inno Setup 6). Lo arma GitHub Actions; no hace falta abrirlo a mano.
; Se instala solo para el usuario actual: no pide permisos de administrador.
#ifndef Version
  #define Version "0.0.0"
#endif

[Setup]
AppId={{6B1E2B47-2F7A-4C57-9C1D-D0A7E5A1D1C5}
AppName=D-MIKE
AppVersion={#Version}
AppPublisher=D-MIKE
DefaultDirName={localappdata}\Programs\D-MIKE
DefaultGroupName=D-MIKE
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=salida
OutputBaseFilename=D-MIKE-instalador-{#Version}
SetupIconFile=..\app\datos\icono.ico
UninstallDisplayIcon={app}\D-MIKE.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ChangesAssociations=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\D-MIKE\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "MicrosoftEdgeWebview2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: FaltaWebView2

[Icons]
Name: "{group}\D-MIKE"; Filename: "{app}\D-MIKE.exe"
Name: "{userdesktop}\D-MIKE"; Filename: "{app}\D-MIKE.exe"; Tasks: escritorio

[Registry]
; Doble clic en un archivo .dmike abre D-MIKE
Root: HKCU; Subkey: "Software\Classes\.dmike"; ValueType: string; ValueData: "DMIKE.Proyecto"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\DMIKE.Proyecto"; ValueType: string; ValueData: "Proyecto de D-MIKE"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\DMIKE.Proyecto\DefaultIcon"; ValueType: string; ValueData: "{app}\D-MIKE.exe,0"
Root: HKCU; Subkey: "Software\Classes\DMIKE.Proyecto\shell\open\command"; ValueType: string; ValueData: """{app}\D-MIKE.exe"" ""%1"""

[Run]
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Instalando el componente WebView2 de Microsoft..."; Check: FaltaWebView2
Filename: "{app}\D-MIKE.exe"; Description: "Abrir D-MIKE"; Flags: nowait postinstall skipifsilent

[Code]
const WV2 = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';
function TieneClave(Raiz: Integer; Ruta: String): Boolean;
var v: String;
begin
  Result := RegQueryStringValue(Raiz, Ruta, 'pv', v) and (v <> '') and (v <> '0.0.0.0');
end;
function FaltaWebView2: Boolean;
begin
  Result := not (TieneClave(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\' + WV2) or
                 TieneClave(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\' + WV2) or
                 TieneClave(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\' + WV2));
end;
