"""Native file selection using only the Python standard library."""
import json
import subprocess
from pathlib import PureWindowsPath
import sys

def _windows_structure():
    import ctypes
    from ctypes import wintypes as wt
    class OPENFILENAMEW(ctypes.Structure):
        _fields_=[('lStructSize',wt.DWORD),('hwndOwner',wt.HWND),('hInstance',wt.HINSTANCE),
        ('lpstrFilter',wt.LPCWSTR),('lpstrCustomFilter',wt.LPWSTR),('nMaxCustFilter',wt.DWORD),
        ('nFilterIndex',wt.DWORD),('lpstrFile',wt.LPWSTR),('nMaxFile',wt.DWORD),
        ('lpstrFileTitle',wt.LPWSTR),('nMaxFileTitle',wt.DWORD),('lpstrInitialDir',wt.LPCWSTR),
        ('lpstrTitle',wt.LPCWSTR),('Flags',wt.DWORD),('nFileOffset',wt.WORD),
        ('nFileExtension',wt.WORD),('lpstrDefExt',wt.LPCWSTR),('lCustData',ctypes.c_ssize_t),
        ('lpfnHook',ctypes.c_void_p),('lpTemplateName',wt.LPCWSTR),('pvReserved',ctypes.c_void_p),
        ('dwReserved',wt.DWORD),('FlagsEx',wt.DWORD)]
    return OPENFILENAMEW

def decode_selection(raw):
    parts=raw.split('\0\0',1)[0].split('\0')
    if not parts or not parts[0]: return []
    if len(parts)==1: return parts
    return [str(PureWindowsPath(parts[0])/name) for name in parts[1:] if name]

def _windows_files(kind,multiple):
    import ctypes
    from ctypes import wintypes as wt
    OPENFILENAMEW=_windows_structure()
    api=ctypes.WinDLL('comdlg32',use_last_error=True)
    user=ctypes.WinDLL('user32',use_last_error=True)
    api.GetOpenFileNameW.argtypes=[ctypes.POINTER(OPENFILENAMEW)];api.GetOpenFileNameW.restype=wt.BOOL
    api.CommDlgExtendedError.argtypes=[];api.CommDlgExtendedError.restype=wt.DWORD
    user.GetActiveWindow.argtypes=[];user.GetActiveWindow.restype=wt.HWND
    buffer=ctypes.create_unicode_buffer(65536)
    config=OPENFILENAMEW();config.lStructSize=ctypes.sizeof(config)
    config.hwndOwner=user.GetActiveWindow()
    config.lpstrFilter='FBX meshes\0*.fbx\0\0' if kind=='mesh' else 'VAT textures\0*.exr;*.png\0\0'
    config.lpstrFile=ctypes.cast(buffer,wt.LPWSTR);config.nMaxFile=len(buffer)
    config.lpstrTitle='Select VAT meshes' if kind=='mesh' else 'Select VAT textures'
    config.Flags=0x80000|0x1000|0x800|0x8|0x4|(0x200 if multiple else 0)
    if not api.GetOpenFileNameW(ctypes.byref(config)):
        error=api.CommDlgExtendedError()
        if error: raise RuntimeError(f'Windows file dialog failed (0x{error:04X})')
        return []
    return decode_selection(buffer[:])

MAC_SCRIPT='''
function run(argv) {
    var app = Application.currentApplication();
    app.includeStandardAdditions = true;
    try {
        var files = app.chooseFile({
            withPrompt: argv[0] === "mesh" ? "Select VAT meshes" : "Select VAT textures",
            ofType: argv[0] === "mesh" ? ["fbx"] : ["exr", "png"],
            multipleSelectionsAllowed: argv[1] === "true",
            invisibles: false,
            showingPackageContents: false
        });
        if (!Array.isArray(files)) files = [files];
        return JSON.stringify(files.map(function(file) { return file.toString(); }));
    } catch (error) {
        if (Number(error.number) === -128) return "[]";
        throw error;
    }
}
'''

def _mac_files(kind,multiple):
    try:
        result=subprocess.run(['/usr/bin/osascript','-l','JavaScript','-e',MAC_SCRIPT,
                               kind,'true' if multiple else 'false'],
                              capture_output=True,text=True,encoding='utf-8',shell=False)
    except OSError as exc:
        raise RuntimeError('macOS file picker unavailable.') from exc
    if result.returncode:
        raise RuntimeError('macOS file picker failed: '+result.stderr.strip())
    try:
        paths=json.loads(result.stdout)
    except (ValueError,TypeError) as exc:
        raise RuntimeError('Invalid macOS file picker response.') from exc
    if not isinstance(paths,list) or any(not isinstance(p,str) or not p for p in paths):
        raise RuntimeError('Invalid macOS file selection.')
    return paths

def choose_files(kind,multiple=False):
    if kind not in ('mesh','texture'): raise ValueError('Unknown picker type')
    if sys.platform=='win32': paths=_windows_files(kind,multiple)
    elif sys.platform=='darwin': paths=_mac_files(kind,multiple)
    else: raise RuntimeError('File browsing is unavailable on this platform.')
    if not multiple and len(paths)>1: raise RuntimeError('Select only one file for this mode.')
    if any('\n' in p or '\r' in p for p in paths):
        raise ValueError('Filenames containing line breaks are unsupported. Rename the file before importing.')
    return paths
