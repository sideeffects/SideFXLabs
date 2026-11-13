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
_shared_field=None
_shared_picker=None
_shared_row=None
_reuse_field=None
_widget_ready=False

@unreal.uclass()
class LabsVatSharedFolderOptions(unreal.Object):
    folder=unreal.uproperty(unreal.DirectoryPath,meta=dict(ContentDir='',DisplayName='Folder',Category='VAT'))

def choose_shared_folder(current):
    options=LabsVatSharedFolderOptions()
    options.set_editor_property('folder',unreal.DirectoryPath(path=current or '/Game'))
    view=unreal.EditorDialogLibraryObjectDetailsViewOptions(show_object_name=False,allow_search=False,allow_resizing=True,min_width=520,min_height=150)
    if not unreal.EditorDialog.show_object_details_view('Shared Dependencies',options,view): return None
    value=options.get_editor_property('folder').path.strip()
    if value:
        from labs_vat_library import check_folder
        check_folder(value)
    return value

def browse_shared_folder():
    widget=active_widget()
    if _busy or not widget or not _widget_ready: return
    try:
        value=choose_shared_folder(str(_shared_field.get_text()))
        if value is not None and active_widget()==widget:
            _shared_field.set_text(value)
            remember_settings(refresh=False)
    except Exception as exc:
        if active_widget()==widget: widget.get_editor_property('Status').set_text(str(exc))
        unreal.log_error('VAT shared folder: '+str(exc))

def add_shared_folder_controls(widget):
    global _shared_field,_shared_picker,_shared_row,_reuse_field
    interpolation=widget.get_editor_property('Interpolate')
    checkbox_style=interpolation.get_editor_property('widget_style')
    for state in ('unchecked','checked','undetermined','background'):
        for interaction in ('','_hovered','_pressed'):
            name=state+interaction+'_image'
            brush=checkbox_style.get_editor_property(name)
            outline=brush.get_editor_property('outline_settings')
            shade=0.45 if interaction else 0.22
            outline.set_editor_property('color',unreal.SlateColor(specified_color=unreal.LinearColor(shade,shade,shade,1)))
            brush.set_editor_property('outline_settings',outline)
            checkbox_style.set_editor_property(name,brush)
    interpolation.set_editor_property('widget_style',checkbox_style)
    root=widget.get_editor_property('Destination').get_parent().get_parent()
    if not isinstance(root,unreal.VerticalBox):
        raise RuntimeError('Could not locate VAT settings panel')
    if _shared_row is not None and unreal.SystemLibrary.is_valid(_shared_row):
        _shared_row.remove_from_parent()
    if _reuse_field is not None and unreal.SystemLibrary.is_valid(_reuse_field):
        _reuse_field.remove_from_parent()
    _shared_row=unreal.new_object(unreal.HorizontalBox,outer=widget)
    help_text='Optional project-owned VAT material library. First use copies all five masters and their functions; later imports reuse them without overwriting your edits. Save customizations and preserve required parameter names. Leave empty to use plugin dependencies.'
    label=unreal.new_object(unreal.TextBlock,outer=widget)
    label.set_text('Shared Dependencies')
    font=label.get_editor_property('font');font.size=11;label.set_font(font)
    label.set_color_and_opacity(unreal.SlateColor(specified_color=unreal.LinearColor(0.9,0.9,0.9,1)))
    label.set_tool_tip_text(help_text)
    slot=_shared_row.add_child_to_horizontal_box(label)
    slot.set_padding(unreal.Margin(12,0,12,0))
    slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
    _shared_field=unreal.new_object(unreal.EditableTextBox,outer=widget)
    _shared_field.set_editor_property('widget_style',widget.get_editor_property('Destination').get_editor_property('widget_style'))
    _shared_field.set_hint_text('Optional')
    _shared_field.set_tool_tip_text(help_text+' Example: /Game/VATShared.')
    slot=_shared_row.add_child_to_horizontal_box(_shared_field)
    slot.set_size(unreal.SlateChildSize(size_rule=unreal.SlateSizeRule.FILL))
    _shared_picker=unreal.new_object(unreal.Button,outer=widget)
    _shared_picker.set_editor_property('widget_style',widget.get_editor_property('Import').get_editor_property('widget_style'))
    _shared_picker.set_tool_tip_text('Choose a project content folder using Unreal’s native folder picker.')
    button_label=unreal.new_object(unreal.TextBlock,outer=widget)
    button_label.set_text('Browse…')
    button_label.set_font(font)
    button_label.set_color_and_opacity(unreal.SlateColor(specified_color=unreal.LinearColor(0.9,0.9,0.9,1)))
    _shared_picker.add_child(button_label)
    _shared_row.add_child_to_horizontal_box(_shared_picker).set_padding(unreal.Margin(6,0,0,0))
    _shared_field.on_text_changed.add_callable(shared_folder_changed)
    _shared_picker.on_clicked.add_callable(browse_shared_folder)
    children=list(root.get_all_children())
    tail=[]
    insertion=next((i for i,c in enumerate(children) if c==widget.get_editor_property('MaterialName').get_parent()),len(children))
    for child in children[insertion:]:
        padding=child.slot.get_editor_property('padding')
        tail.append((child,padding))
        root.remove_child(child)
    root.add_child_to_vertical_box(_shared_row).set_padding(unreal.Margin(0,6,0,8))
    _reuse_field=unreal.new_object(unreal.CheckBox,outer=widget)
    _reuse_field.set_editor_property('widget_style',widget.get_editor_property('Interpolate').get_editor_property('widget_style'))
    _reuse_field.set_is_checked(True)
    _reuse_field.set_tool_tip_text('Use the selected mode’s shared master, or the plugin master if no shared folder is set. Turn off to create a separate master per import. A new material instance is always created. Without a shared folder, materials still depend on Labs.')
    reuse_label=unreal.new_object(unreal.TextBlock,outer=widget)
    reuse_label.set_text('Reuse Master Material')
    reuse_label.set_font(font)
    reuse_label.set_color_and_opacity(unreal.SlateColor(specified_color=unreal.LinearColor(0.9,0.9,0.9,1)))
    _reuse_field.add_child(reuse_label)
    _reuse_field.on_check_state_changed.add_callable(reuse_changed)
    root.add_child_to_vertical_box(_reuse_field).set_padding(unreal.Margin(12,0,0,6))
    for child,padding in tail:
        if child==widget.get_editor_property('Interpolate'):
            wrapper=unreal.new_object(unreal.HorizontalBox,outer=widget)
            wrapper.set_visibility(unreal.SlateVisibility.VISIBLE)
            wrapper.add_child_to_horizontal_box(child)
            child=wrapper
        root.add_child_to_vertical_box(child).set_padding(padding)

def shared_folder_changed(text):
    if not _restoring: remember_settings(refresh=False)

def reuse_changed(checked):
    if not _restoring: remember_settings(refresh=False)

def active_widget():
    global _widget
    if _widget is not None and not unreal.SystemLibrary.is_valid(_widget):
        _widget=None
    return _widget

def widget_constructed(path):
    global _widget,_restoring,_widget_ready
    widget=unreal.find_object(None,path)
    if widget is None or not unreal.SystemLibrary.is_valid(widget):
        raise RuntimeError('Could not initialize the VAT importer widget')
    _widget=widget
    _widget_ready=False
    _restoring=True
    try:
        add_shared_folder_controls(widget)
        if 'Mode' not in _session:
            widget.get_editor_property('Mode').set_selected_option(Settings().mode)
        for name,value in _session.items():
            if name=='ReuseMasterMaterial':
                _reuse_field.set_is_checked(value)
                continue
            if name=='SharedDependencies':
                _shared_field.set_text(value)
                continue
            if name=='Destination' and value=='/Game/VATPythonPrototype': value='/Game/VAT'
            field=widget.get_editor_property(name)
            if name=='Mode': field.set_selected_option(value)
            elif name=='Interpolate': field.set_is_checked(value)
            else: field.set_text(value)
        _widget_ready=True
    except Exception:
        _widget=None
        raise
    finally:
        _restoring=False
    settings_changed()

def widget_destructed(path):
    global _widget,_widget_ready,_shared_field,_shared_picker,_shared_row,_reuse_field
    widget=active_widget()
    if widget is None or widget.get_path_name()!=path: return
    try:
        remember_settings(refresh=False)
    finally:
        if _widget is widget:
            _widget=None
            _widget_ready=False
            _shared_field=None
            _shared_picker=None
            _shared_row=None
            _reuse_field=None

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

def remember_settings(refresh=True):
    global _session
    if not active_widget() or _restoring or not _widget_ready: return False
    values={}
    for name in ['Mode','Meshes','Textures','Destination','MaterialName','FPS','Interpolate']:
        field=_widget.get_editor_property(name)
        if field is None or not unreal.SystemLibrary.is_valid(field): return False
        values[name]=field.get_selected_option() if name=='Mode' else (field.is_checked() if name=='Interpolate' else str(field.get_text()))
    if _shared_field is not None and unreal.SystemLibrary.is_valid(_shared_field):
        values['SharedDependencies']=str(_shared_field.get_text())
    if _reuse_field is not None and unreal.SystemLibrary.is_valid(_reuse_field):
        values['ReuseMasterMaterial']=_reuse_field.is_checked()
    _session=values
    if _session.get('Destination')=='/Game/VATPythonPrototype':
        _session['Destination']='/Game/VAT'
    if refresh: refresh_file_lists()
    return True

def settings_changed():
    if _restoring or not active_widget(): return
    if not remember_settings(): return
    control=_widget.get_editor_property('Interpolate')
    control.set_is_enabled(_session['Mode']!='Fluid')
    help_text='Fluid uses its existing playback decoding; this function has no interpolation switch.' if _session['Mode']=='Fluid' else 'Blend between animation frames.'
    control.set_tool_tip_text(help_text)
    control.get_parent().set_tool_tip_text(help_text)
    _widget.get_editor_property('InterpolationHelp').set_visibility(unreal.SlateVisibility.COLLAPSED)

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
            material_name=_session['MaterialName'].strip(),fps=float(_session['FPS']),interpolate=_session['Interpolate'],
            shared_dependencies=_session.get('SharedDependencies','').strip(),
            reuse_master_material=_session.get('ReuseMasterMaterial',True))
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
