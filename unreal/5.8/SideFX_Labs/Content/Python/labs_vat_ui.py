"""Native Editor Utility Widget adapter; session memory, no runtime dependency."""
import unreal
from pathlib import Path
from labs_vat_importer import Settings, import_vat

WIDGET='/SideFX_Labs/Editor/VATImporter/EUW_VATImporter.EUW_VATImporter_C'
BLUEPRINT='/SideFX_Labs/Editor/VATImporter/EUW_VATImporter.EUW_VATImporter'
_widget=None
_session={}
_busy=False
last_result=None
_restoring=False
_refreshing=False

def active_widget():
    global _widget
    if _widget is not None and not unreal.SystemLibrary.is_valid(_widget):
        _widget=None
    return _widget

def widget_constructed(path):
    global _widget,_restoring
    widget=unreal.find_object(None,path)
    if widget is None or not unreal.SystemLibrary.is_valid(widget):
        raise RuntimeError('Could not initialize the VAT importer widget')
    _widget=widget
    _restoring=True
    try:
        for name,value in _session.items():
            if name=='Destination' and value=='/Game/VATPythonPrototype': value='/Game/VAT'
            field=widget.get_editor_property(name)
            if name=='Mode': field.set_selected_option(value)
            elif name=='Interpolate': field.set_is_checked(value)
            else: field.set_text(value)
    finally:
        _restoring=False
    settings_changed()

def widget_destructed(path):
    global _widget
    widget=active_widget()
    if widget is None or widget.get_path_name()!=path: return
    try:
        remember_settings()
    finally:
        if _widget is widget: _widget=None

def refresh_file_lists():
    global _refreshing
    if not active_widget() or _refreshing or _restoring: return
    _refreshing=True
    try:
        from labs_vat_importer import ROLES
        for field,list_name,count_name in [('Meshes','MeshList','MeshCount'),('Textures','TextureList','TextureCount')]:
            box=_widget.get_editor_property(list_name)
            box.clear_children()
            paths=[s.strip().strip('"') for s in str(_widget.get_editor_property(field).get_text()).splitlines() if s.strip()]
            _widget.get_editor_property(count_name).set_text(str(len(paths))+' selected')
            for path in paths:
                name=Path(path).name
                role=ROLES.get(Path(path).stem.casefold().split('_')[-1],'Unrecognized') if field=='Textures' else 'FBX'
                row=unreal.new_object(unreal.TextBlock,outer=_widget)
                row.set_text(name+'  ('+role+')')
                row.set_tool_tip_text(path)
                row.set_auto_wrap_text(True)
                font=row.get_editor_property('font');font.size=11;row.set_font(font)
                row.set_color_and_opacity(unreal.SlateColor(specified_color=unreal.LinearColor(0.9,0.9,0.9,1)))
                box.add_child_to_vertical_box(row).set_padding(unreal.Margin(6,3,6,3))
    finally: _refreshing=False

def toggle_manual():
    if not active_widget(): return
    panel=_widget.get_editor_property('ManualPaths')
    visible=panel.get_visibility()!=unreal.SlateVisibility.COLLAPSED
    panel.set_visibility(unreal.SlateVisibility.COLLAPSED if visible else unreal.SlateVisibility.VISIBLE)

def remember_settings():
    global _session
    if not active_widget() or _restoring: return
    values={}
    for name in ['Mode','Meshes','Textures','Destination','MaterialName','FPS','Interpolate']:
        field=_widget.get_editor_property(name)
        values[name]=field.get_selected_option() if name=='Mode' else (field.is_checked() if name=='Interpolate' else str(field.get_text()))
    _session=values
    if _session.get('Destination')=='/Game/VATPythonPrototype':
        _session['Destination']='/Game/VAT'
    refresh_file_lists()

def settings_changed():
    if _restoring or not active_widget(): return
    remember_settings()
    _widget.get_editor_property('Interpolate').set_is_enabled(_session['Mode']!='Fluid')
    _widget.get_editor_property('InterpolationHelp').set_text('Fluid uses its existing playback decoding; this function has no interpolation switch.' if _session['Mode']=='Fluid' else 'Blend between animation frames.')

def browse(kind):
    if _busy or not active_widget(): return
    try:
        from labs_vat_picker import choose_files
        mode=_widget.get_editor_property('Mode').get_selected_option()
        files=choose_files(kind,multiple=(kind=='texture' or mode=='Skeletal'))
        if files:
            _widget.get_editor_property('Meshes' if kind=='mesh' else 'Textures').set_text('\n'.join(files))
            remember_settings()
    except Exception as exc:
        _widget.get_editor_property('ManualPaths').set_visibility(unreal.SlateVisibility.VISIBLE)
        _widget.get_editor_property('Status').set_text(str(exc)+' Use Edit file paths manually to continue.')
        unreal.log_error('VAT file selection: '+str(exc))

def open_widget():
    global _widget,_restoring
    remember_settings()
    try:
        blueprint=unreal.load_asset(BLUEPRINT)
        if not isinstance(blueprint,unreal.EditorUtilityWidgetBlueprint):
            raise RuntimeError('Missing VAT importer widget asset: '+BLUEPRINT)
        subsystem=unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
        old_tab=unreal.Name(WIDGET+'_ActiveTab')
        if subsystem.does_tab_exist(old_tab):
            subsystem.unregister_tab_by_id(old_tab)
        widget=subsystem.spawn_and_register_tab(blueprint)
        if not widget:
            raise RuntimeError('Could not open VAT Importer; finish changing levels and try again')
        if active_widget()!=widget:
            widget_constructed(widget.get_path_name())
        return widget
    finally:
        _restoring=False

def import_from_open_widget():
    global _busy,last_result,_session
    if _busy: return None
    if not active_widget(): raise RuntimeError('Open the VAT importer through its SideFX Labs menu entry')
    fields={name:_widget.get_editor_property(name) for name in ['Mode','Meshes','Textures','Destination','MaterialName','FPS','Status','Import','Interpolate']}
    remember_settings()
    _busy=True;fields['Import'].set_is_enabled(False)
    try:
        settings=Settings(mode=_session['Mode'],meshes=_session['Meshes'].splitlines(),
            textures=_session['Textures'].splitlines(),destination=_session['Destination'].strip(),
            material_name=_session['MaterialName'].strip(),fps=float(_session['FPS']),interpolate=_session['Interpolate'])
        settings.meshes=[s for s in settings.meshes if s.strip()]
        settings.textures=[s for s in settings.textures if s.strip()]
        last_result=import_vat(settings)
        fields['Status'].set_text('Saved '+str(len(last_result['meshes']))+' mesh(es) and VAT material assets.')
        return last_result
    except Exception as exc:
        last_result={'error':str(exc)}
        fields['Status'].set_text('Import failed: '+str(exc))
        unreal.log_error('VAT Python: '+str(exc))
        return last_result
    finally:
        _busy=False;fields['Import'].set_is_enabled(True)

@unreal.uclass()
class LabsVatPythonMenuEntry(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self,context):
        open_widget()

_entry=None
def register_menu():
    global _entry
    menus=unreal.ToolMenus.get()
    owner='SideFXLabsVATImporter'
    menus.unregister_owner_by_name(owner)
    menu=menus.extend_menu('LevelEditor.MainMenu.SidefxLabsEditor_SubMenu')
    menu.add_section('SideFXLabsPlugins','Plugins')
    _entry=LabsVatPythonMenuEntry()
    _entry.init_entry(owner,'LevelEditor.MainMenu.SidefxLabsEditor_SubMenu','SideFXLabsPlugins',
        'SideFXLabsVAT_Importer','VAT Importer','Import Houdini VAT meshes and textures')
    _entry.register_menu_entry()
    menus.refresh_all_widgets()
