import json
import re
import unreal
from labs_vat_exr import ValidationError

MODES=('Soft','Rigid','Fluid','Sprite','Skeletal')
ROOT='/SideFX_Labs/'
KEY='SideFXLabs.VAT.SharedLibrary'
VERSION=1
E=unreal.EditorAssetLibrary
L=unreal.MaterialEditingLibrary

def source_master(mode):
    return ROOT+'Editor/VATImporter/Materials/M_Import_'+mode

def package(obj):
    return obj.get_path_name().split('.')[0]

def expressions(asset):
    prefix=asset.get_path_name()+':'
    return [x for x in unreal.ObjectIterator(unreal.MaterialExpression)
            if x.get_outer()==asset or x.get_path_name().startswith(prefix)]

def references(asset):
    for expr in expressions(asset):
        if isinstance(expr,unreal.MaterialExpressionMaterialFunctionCall):
            value=expr.get_editor_property('material_function')
            if value: yield expr,'material_function',value
        for prop in ('texture','font'):
            try: value=expr.get_editor_property(prop)
            except Exception: continue
            if isinstance(value,unreal.Object): yield expr,prop,value

def check_folder(folder):
    if not re.fullmatch(r'/Game/[A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)*',folder):
        raise ValidationError('Shared Dependencies Folder must be a subfolder of /Game, for example /Game/VATShared')
    return folder

def master_path(folder,mode):
    return folder+'/Materials/M_Import_'+mode

def dependencies(paths):
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,
        include_hard_package_references=True,include_searchable_names=False,
        include_soft_management_references=False,include_hard_management_references=False)
    seen=set()
    dirty={x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
    todo=list(paths)
    while todo:
        p=todo.pop()
        if p in seen or p.startswith('/Script/'): continue
        seen.add(p)
        if p.startswith(ROOT): raise ValidationError('Shared material still depends on Labs: '+p)
        if not p.startswith(('/Game/','/Engine/')): raise ValidationError('Shared material requires another plugin: '+p)
        if not E.does_asset_exist(p): raise ValidationError('Missing material dependency: '+p)
        if p in dirty:
            raise ValidationError('Save material dependency edits before importing: '+p)
        obj=unreal.load_asset(p)
        if obj is None: raise ValidationError('Could not load material dependency: '+p)
        if isinstance(obj,(unreal.Material,unreal.MaterialFunction)):
            todo.extend(package(value) for _,_,value in references(obj))
        elif isinstance(obj,unreal.MaterialInstanceConstant):
            parent=obj.get_editor_property('parent')
            if parent: todo.append(package(parent))
            todo.extend(package(value) for name in L.get_texture_parameter_names(obj)
                        if (value:=L.get_material_instance_texture_parameter_value(obj,name)) is not None)
        todo.extend(str(d) for d in registry.get_dependencies(p,options) or [])
    return seen

def validate_interface(material,mode,roles=()):
    scalar={'Houdini FPS','Playback Speed','Game Time at First Frame','Use Playback Controls'}
    switches={'Support Legacy Parameters and Instancing','Auto Playback'}
    if mode=='Fluid':
        scalar.add('Velocity Source FPS')
        switches.update(('Velocity Texture Available','Support Custom Motion Blur'))
    elif mode=='Skeletal':
        switches.update(('Interframe Interpolation','Use Packed Animation Clips','Animaiton Transition',
                         'Mode: DQS','Mode: LBS from Matrix Map','Use Compressed Normals','Support Surface Normal Maps'))
    else:
        switches.update(('Interframe Interpolation','Positions Require Two Textures'))
        if mode=='Rigid': switches.add('Animate First Frame')
    required_textures={'Position Texture','Color Texture'} if mode=='Sprite' else {'Position Texture','Rotation Texture'}
    if mode=='Fluid': required_textures.update(('Lookup Table','Velocity Texture'))
    required_textures.update(roles)
    for label,required,getter in (('scalar',scalar,L.get_scalar_parameter_names),
        ('switch',switches,L.get_static_switch_parameter_names),('texture',required_textures,L.get_texture_parameter_names)):
        missing=required-{str(n) for n in getter(material)}
        if missing: raise ValidationError('Incompatible shared '+mode+' material; missing '+label+': '+', '.join(sorted(missing)))

def load_library(folder):
    anchor=unreal.load_asset(master_path(folder,'Soft'))
    if not isinstance(anchor,unreal.Material): raise ValidationError('Incomplete or unrecognized shared library: '+folder)
    raw=E.get_metadata_tag(anchor,KEY)
    try: record=json.loads(raw)
    except Exception: raise ValidationError('Unrecognized shared library. Choose an empty folder or an existing VAT shared library.')
    if not isinstance(record,dict) or record.get('version')!=VERSION or record.get('root')!=folder or not isinstance(record.get('assets'),dict):
        raise ValidationError('Incompatible shared library manifest: '+folder)
    assets={}
    for relative,class_name in record['assets'].items():
        if not isinstance(relative,str) or not re.fullmatch(r'[A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)*',relative):
            raise ValidationError('Invalid shared library asset mapping')
        path=folder+'/'+relative
        obj=unreal.load_asset(path)
        if obj is None or not isinstance(obj,(unreal.Material,unreal.MaterialFunction,unreal.Texture2D)) or obj.get_class().get_name()!=class_name:
            raise ValidationError('Missing or incompatible shared asset: '+path)
        if obj.get_outer() in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():
            raise ValidationError('Save shared material edits before importing: '+path)
        assets[path]=obj
    for mode in MODES:
        path=master_path(folder,mode)
        if path not in assets or not isinstance(assets[path],unreal.Material):
            raise ValidationError('Missing shared master: '+path)
        validate_interface(assets[path],mode)
    dependencies(assets)
    return assets

def ensure_library(folder):
    check_folder(folder)
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous([folder],True)
    existing=E.list_assets(folder,recursive=True,include_folder=False)
    if existing:
        load_library(folder)
        return
    objects={}
    def collect(asset):
        p=package(asset)
        if not p.startswith(ROOT) or p in objects: return
        if not isinstance(asset,(unreal.Material,unreal.MaterialFunction,unreal.Texture2D)):
            raise ValidationError('Unsupported shared dependency type: '+p)
        objects[p]=asset
        for _,_,value in references(asset): collect(value)
    for mode in MODES:
        asset=unreal.load_asset(source_master(mode))
        if not isinstance(asset,unreal.Material): raise ValidationError('Missing importer template: '+source_master(mode))
        collect(asset)
    mapping={p:master_path(folder,p.rsplit('_',1)[-1]) if p in [source_master(m) for m in MODES]
             else folder+'/'+p.removeprefix(ROOT) for p in objects}
    for target in mapping.values():
        if E.does_asset_exist(target): raise ValidationError('Shared asset already exists: '+target)
    copies={}
    try:
        for p,asset in objects.items():
            obj=E.duplicate_loaded_asset(asset,mapping[p])
            if obj is None: raise ValidationError('Could not copy shared asset: '+p)
            copies[p]=obj
        for p,obj in copies.items():
            for expr,prop,value in references(obj):
                if package(value) in copies: expr.set_editor_property(prop,copies[package(value)])
            if isinstance(obj,unreal.Material):
                obj.set_editor_property('preview_mesh',unreal.SoftObjectPath())
        for obj in copies.values():
            if isinstance(obj,unreal.MaterialFunction): L.update_material_function(obj)
        for obj in copies.values():
            if isinstance(obj,unreal.Material): L.recompile_material(obj)
            if not E.save_loaded_asset(obj,False): raise ValidationError('Could not save shared asset: '+package(obj))
        registry.scan_paths_synchronous([folder],True)
        dependencies(mapping.values())
        for mode in MODES: validate_interface(copies[source_master(mode)],mode)
        record={'version':VERSION,'root':folder,'assets':{mapping[p][len(folder)+1:]:obj.get_class().get_name() for p,obj in copies.items()},
                'sources':{p:mapping[p][len(folder)+1:] for p in copies}}
        anchor=copies[source_master('Soft')]
        E.set_metadata_tag(anchor,KEY,json.dumps(record,sort_keys=True))
        if not E.save_loaded_asset(anchor,False): raise ValidationError('Could not save shared library manifest')
    except Exception:
        unreal.log_error('Shared library initialization failed. Partial copies retained in '+folder+'. Choose a new empty folder or inspect these assets; no plugin fallback was used.')
        raise
