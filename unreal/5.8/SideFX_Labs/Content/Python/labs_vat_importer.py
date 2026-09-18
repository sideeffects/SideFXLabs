from dataclasses import dataclass, field
from pathlib import Path
import math
import re
import unreal
from labs_vat_exr import ValidationError, velocity_info

LIB=unreal.MaterialEditingLibrary
ASSETS=unreal.AssetToolsHelpers.get_asset_tools()
ROLES={'pos':'Position Texture','rot':'Rotation Texture','col':'Color Texture',
       'lookup':'Lookup Table','vel':'Velocity Texture','pos2':'Position Texture 2','col2':'Spare Color Texture'}

@dataclass
class Settings:
    mode: str='Fluid'
    meshes: list=field(default_factory=list)
    textures: list=field(default_factory=list)
    destination: str='/Game/VAT'
    material_name: str='HoudiniVAT'
    fps: float=24.0
    interpolate: bool=True
    loop: bool=True


def canonical_files(paths):
    result=[]
    for path in paths:
        raw=str(path)
        if '\n' in raw or '\r' in raw:
            raise ValidationError('Filenames containing line breaks are unsupported. Rename the file before importing.')
        p=Path(raw)
        if not p.is_file():
            raw=raw.strip()
            if len(raw)>=2 and raw[0]==raw[-1]=='"': raw=raw[1:-1]
            p=Path(raw)
        p=p.resolve()
        if not p.is_file(): raise ValidationError(f'File does not exist: {p}')
        if not any(p.samefile(existing) for existing in result): result.append(p)
    return result


def preflight(settings):
    if settings.mode not in ('Soft','Rigid','Fluid','Sprite','Skeletal'):
        raise ValidationError('Choose a supported VAT mode')
    meshes=canonical_files(settings.meshes)
    if not meshes or (settings.mode!='Skeletal' and len(meshes)!=1):
        raise ValidationError('Choose one mesh, or one or more meshes for Skeletal mode')
    if any(p.suffix.lower()!='.fbx' for p in meshes): raise ValidationError('Mesh inputs must be FBX')
    if not re.fullmatch(r'/Game(?:/[A-Za-z0-9_]+)*',settings.destination):
        raise ValidationError('Destination must be a valid /Game package folder')
    if not math.isfinite(settings.fps) or settings.fps<=0: raise ValidationError('Houdini FPS must be positive and finite')
    textures={}
    for path in canonical_files(settings.textures):
        if path.suffix.lower() not in ('.exr','.png'): raise ValidationError('Use EXR or PNG textures')
        role=ROLES.get(path.stem.casefold().split('_')[-1])
        if role=='Velocity Texture' and not path.stem.casefold().endswith('_vel'):
            raise ValidationError('Velocity filenames must end with _vel')
        if not role: raise ValidationError(f'Unrecognized texture suffix: {path.name}')
        if role in textures: raise ValidationError(f'Multiple {role} textures selected')
        textures[role]=path
    required={'Position Texture','Color Texture'} if settings.mode=='Sprite' else {'Position Texture','Rotation Texture'}
    if settings.mode=='Fluid': required.add('Lookup Table')
    if not required.issubset(textures): raise ValidationError('Missing required textures: '+', '.join(sorted(required-set(textures))))
    if settings.mode=='Skeletal' and set(textures)!=required:
        raise ValidationError('Packed Skeletal mode accepts one shared Position/Rotation pair')
    velocity=None
    if 'Velocity Texture' in textures:
        if settings.mode!='Fluid': raise ValidationError('Velocity texture is supported only for Fluid')
        if textures['Velocity Texture'].suffix.lower()!='.exr': raise ValidationError('Velocity must be EXR')
        velocity=velocity_info(textures['Velocity Texture'],textures['Position Texture'],settings.fps)
    template=f'/SideFX_Labs/Editor/VATImporter/Materials/M_Import_{settings.mode}'
    if not unreal.load_asset(template): raise ValidationError('Missing prewired importer template: '+template)
    available={str(n) for n in LIB.get_texture_parameter_names(unreal.load_asset(template))}
    if not set(textures).issubset(available):
        raise ValidationError('Unsupported textures for this mode: '+', '.join(sorted(set(textures)-available)))
    return meshes,textures,velocity,template


def unique_path(folder,name):
    name=re.sub(r'[^A-Za-z0-9_]','_',name)
    return ASSETS.create_unique_asset_name(folder+'/'+name,'')


def import_file(path,folder,mesh=False):
    package,name=unique_path(folder,path.stem)
    task=unreal.AssetImportTask()
    task.set_editor_properties({'filename':str(path),'destination_path':folder,'destination_name':name,
                                'automated':True,'replace_existing':False,'save':False})
    if mesh:
        opts=unreal.FbxImportUI()
        opts.set_editor_properties({'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,
             'import_as_skeletal':False,'import_mesh':True,'import_animations':False,
             'import_materials':False,'import_textures':False,'automated_import_should_detect_type':False})
        opts.static_mesh_import_data.set_editor_properties({
            'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS,
            'vertex_color_import_option':unreal.VertexColorImportOption.REPLACE,
            'generate_lightmap_u_vs':False,'remove_degenerates':False,'build_nanite':False,
            'combine_meshes':True,'auto_generate_collision':False})
        task.set_editor_properties({'factory':unreal.FbxFactory(),'options':opts})
    else:
        task.set_editor_property('factory',unreal.TextureFactory())
    ASSETS.import_asset_tasks([task])
    expected=unreal.StaticMesh if mesh else unreal.Texture2D
    objects=[o for o in task.get_objects() if isinstance(o,expected)]
    if len(objects)!=1: raise RuntimeError(f'Expected one {expected.__name__} from {path}, got {len(objects)}')
    return objects[0]


def configure_mesh(mesh):
    subsystem=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for lod in range(subsystem.get_lod_count(mesh)):
        settings=subsystem.get_lod_build_settings(mesh,lod)
        settings.set_editor_properties({'generate_lightmap_u_vs':False,'remove_degenerates':False,
            'recompute_normals':False,'recompute_tangents':False,'use_full_precision_u_vs':True,
            'use_backwards_compatible_f16_trunc_u_vs':False})
        subsystem.set_lod_build_settings(mesh,lod,settings)


def configure_texture(texture,path,velocity=False):
    exr=path.suffix.lower()=='.exr'
    texture.set_editor_properties({'filter':unreal.TextureFilter.TF_NEAREST,'srgb':False,
        'mip_gen_settings':unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS,
        'lod_group':unreal.TextureGroup.TEXTUREGROUP_16_BIT_DATA if exr else unreal.TextureGroup.TEXTUREGROUP_8_BIT_DATA,
        'compression_settings':unreal.TextureCompressionSettings.TC_HDR_F32 if velocity else (
            unreal.TextureCompressionSettings.TC_HDR if exr else unreal.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP)})


def assign_instance(mesh,instance):
    slots=list(mesh.get_editor_property('static_materials'))
    if not slots: slots=[unreal.StaticMaterial(material_interface=instance)]
    else:
        for slot in slots: slot.set_editor_property('material_interface',instance)
    mesh.set_editor_property('static_materials',slots)


def import_vat(settings):
    meshes,texture_paths,velocity,template=preflight(settings)
    created=[]
    try:
        with unreal.ScopedSlowTask(len(meshes)+len(texture_paths)+2,'Importing VAT assets') as progress:
            imported_meshes=[]
            for path in meshes:
                progress.enter_progress_frame(1,str(path.name))
                mesh=import_file(path,settings.destination,True);created.append(mesh)
                configure_mesh(mesh);imported_meshes.append(mesh)
            textures={}
            for role,path in texture_paths.items():
                progress.enter_progress_frame(1,str(path.name))
                tex=import_file(path,settings.destination);created.append(tex)
                configure_texture(tex,path,role=='Velocity Texture');textures[role]=tex
            name=settings.material_name
            if not name.startswith('M_'): name='M_'+name
            material_path,material_name=unique_path(settings.destination,name)
            material=unreal.EditorAssetLibrary.duplicate_asset(template,material_path)
            if not material: raise RuntimeError('Material duplication failed')
            created.append(material)
            if settings.mode=='Fluid':
                calls=[e for e in LIB.get_material_expressions(material) if isinstance(e,unreal.MaterialExpressionMaterialFunctionCall)]
                if len(calls)!=1: raise RuntimeError('Expected one Fluid function call')
                node=LIB.create_material_expression(material,unreal.MaterialExpressionStaticBool,-950,500)
                node.set_editor_property('value',velocity is not None)
                if not LIB.connect_material_expressions(node,'',calls[0],'Velocity Texture Available'):
                    raise RuntimeError('Missing Velocity Texture Available input')
            LIB.recompile_material(material)
            progress.enter_progress_frame(1,'Material')
            _,instance_name=unique_path(settings.destination,'MI_'+material_name.removeprefix('M_'))
            instance=ASSETS.create_asset(instance_name,settings.destination,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
            if not instance: raise RuntimeError('Material instance creation failed')
            created.append(instance)
            LIB.set_material_instance_parent(instance,material)
            scalar_names={str(n) for n in LIB.get_scalar_parameter_names(material)}
            switch_names={str(n) for n in LIB.get_static_switch_parameter_names(material)}
            texture_names={str(n) for n in LIB.get_texture_parameter_names(material)}
            def scalar(name,value):
                if name not in scalar_names: raise RuntimeError('Missing scalar: '+name)
                LIB.set_material_instance_scalar_parameter_value(instance,name,value)
                if not math.isclose(LIB.get_material_instance_scalar_parameter_value(instance,name),value,rel_tol=1e-6,abs_tol=1e-6):
                    raise RuntimeError('Scalar assignment failed: '+name)
            def switch(name,value):
                if name not in switch_names: raise RuntimeError('Missing switch: '+name)
                LIB.set_material_instance_static_switch_parameter_value(instance,name,value)
                if LIB.get_material_instance_static_switch_parameter_value(instance,name)!=value: raise RuntimeError('Switch assignment failed: '+name)
            scalar('Houdini FPS',velocity['fps'] if velocity else settings.fps)
            scalar('Playback Speed',1.0)
            scalar('Game Time at First Frame',0.0)
            scalar('Use Playback Controls',0.0)
            switch('Support Legacy Parameters and Instancing',False)
            switch('Auto Playback',True)
            if settings.mode=='Fluid':
                switch('Support Custom Motion Blur',velocity is not None)
                scalar('Velocity Source FPS',velocity['fps'] if velocity else settings.fps)
            elif settings.mode=='Skeletal':
                switch('Interframe Interpolation',settings.interpolate)
                for key,value in {'Auto Playback':True,'Use Packed Animation Clips':True,
                     'Animaiton Transition':False,'Mode: DQS':False,'Mode: LBS from Matrix Map':False,
                     'Use Compressed Normals':False,'Support Surface Normal Maps':False}.items(): switch(key,value)
            else:
                switch('Interframe Interpolation',settings.interpolate)
                switch('Positions Require Two Textures','Position Texture 2' in textures)
                if settings.mode=='Rigid': switch('Animate First Frame',True)
            for role,tex in textures.items():
                if role not in texture_names: raise RuntimeError('Missing texture parameter: '+role)
                LIB.set_material_instance_texture_parameter_value(instance,role,tex)
                if LIB.get_material_instance_texture_parameter_value(instance,role)!=tex: raise RuntimeError('Texture assignment failed: '+role)
            LIB.update_material_instance(instance)
            for mesh in imported_meshes: assign_instance(mesh,instance)
            for asset in created:
                if not unreal.EditorAssetLibrary.save_loaded_asset(asset,only_if_is_dirty=False): raise RuntimeError('Failed to save '+asset.get_path_name())
            progress.enter_progress_frame(1,'Saved')
        result={'mode':settings.mode,'meshes':[m.get_path_name() for m in imported_meshes],
            'material':material.get_path_name(),'instance':instance.get_path_name(),
            'textures':{k:v.get_path_name() for k,v in textures.items()},'velocity':velocity}
        unreal.log('VAT Python import saved: '+str(result))
        return result
    except Exception:
        unreal.log_error('VAT import failed; partial assets retained for diagnosis: '+str([a.get_path_name() for a in created]))
        raise
