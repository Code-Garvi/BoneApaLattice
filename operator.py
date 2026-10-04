import bpy
import mathutils

def create_armature_for_lattice(context, lattice_obj, only_selected=False, parent_to_active=False):
    if not lattice_obj or lattice_obj.type != 'LATTICE':
        return False, "Please select a Lattice object."

    target_vertices = []
    
    current_mode = lattice_obj.mode
    if current_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    lattice = lattice_obj.data
    
    for i, pt in enumerate(lattice.points):
        if only_selected:
            if pt.select:
                target_vertices.append((i, pt.co_deform.copy()))
        else:
            target_vertices.append((i, pt.co_deform.copy()))
            
    if not target_vertices:
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=current_mode)
        return False, "No vertices targeted (if 'Selected', ensure vertices are selected in Edit mode)."

    # Check if an armature is selected along with the lattice
    selected_armatures = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']
    
    if selected_armatures:
        arm_obj = selected_armatures[0]
        arm_data = arm_obj.data
    else:
        arm_data = bpy.data.armatures.new(name=f"{lattice_obj.name}_Armature")
        arm_obj = bpy.data.objects.new(name=f"{lattice_obj.name}_Armature", object_data=arm_data)
        context.collection.objects.link(arm_obj)
        
        # 1. Strip scaling from the Armature.
        # Non-uniform scales on Armature objects cause massive skewing bugs in Blender.
        # We copy only the location and rotation from the lattice.
        loc, rot, scale = lattice_obj.matrix_world.decompose()
        arm_obj.matrix_world = mathutils.Matrix.LocRotScale(loc, rot, mathutils.Vector((1.0, 1.0, 1.0)))
    
    # Ensure bone collection exists (Blender 4.0+)
    bone_col = None
    if hasattr(arm_data, "collections"):
        bone_col = arm_data.collections.get("latticebones")
        if not bone_col:
            bone_col = arm_data.collections.new("latticebones")

    active_bone_name = None
    if parent_to_active and arm_obj.data.bones.active:
        active_bone_name = arm_obj.data.bones.active.name

    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    context.view_layer.objects.active = arm_obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    active_edit_bone = None
    if active_bone_name:
        active_edit_bone = arm_obj.data.edit_bones.get(active_bone_name)

    bone_names = []
    lattice_mat_world = lattice_obj.matrix_world
    arm_mat_inv = arm_obj.matrix_world.inverted()
    
    for idx, co in target_vertices:
        bone_name = f"Bone_{idx}"
        
        edit_bone = arm_obj.data.edit_bones.new(bone_name)
        
        # The bone name might have changed if there's a name collision
        bone_name = edit_bone.name
        bone_names.append((idx, bone_name))
        
        # 2. Perfect spatial alignment
        # We transform the vertex coordinate (which is in Lattice local space) into World space.
        # Then, we transform it from World space into the Armature's unscaled local space.
        world_co = lattice_mat_world @ co
        arm_local_co = arm_mat_inv @ world_co
        
        edit_bone.head = arm_local_co
        # Add a slight tail thickness for usability
        edit_bone.tail = arm_local_co + mathutils.Vector((0, 0, 0.5))
        
        if parent_to_active and active_edit_bone:
            edit_bone.parent = active_edit_bone

        if bone_col:
            bone_col.assign(edit_bone)
        
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 3. Pure API Parenting to avoid operator context errors
    # We set the parent seamlessly by providing the exact inverse world matrix of the armature.
    if lattice_obj.parent != arm_obj:
        lattice_obj.parent = arm_obj
        lattice_obj.parent_type = 'OBJECT'
        lattice_obj.matrix_parent_inverse = arm_obj.matrix_world.inverted()
    
    # 4. Bind the armature correctly
    has_armature_mod = False
    for mod in lattice_obj.modifiers:
        if mod.type == 'ARMATURE' and mod.object == arm_obj:
            has_armature_mod = True
            break
            
    if not has_armature_mod:
        mod = lattice_obj.modifiers.new(name="Armature", type='ARMATURE')
        mod.object = arm_obj
    
    # 5. Populate the weights map perfectly 1:1
    for idx, bone_name in bone_names:
        vg = lattice_obj.vertex_groups.get(bone_name)
        if not vg:
            vg = lattice_obj.vertex_groups.new(name=bone_name)
        vg.add([idx], 1.0, 'REPLACE')

    bpy.ops.object.select_all(action='DESELECT')
    lattice_obj.select_set(True)
    arm_obj.select_set(True)
    context.view_layer.objects.active = arm_obj
    
    return True, f"Created {len(bone_names)} bones."


class OBJECT_OT_bonify_lattice_all(bpy.types.Operator):
    bl_idname = "object.bonify_lattice_all"
    bl_label = "Bonify All Lattice Vertices"
    bl_description = "Creates bones for all vertices of the active Lattice"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object and context.active_object.type == 'LATTICE':
            return True
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'LATTICE':
                    return True
        return False

    def execute(self, context):
        lattice_obj = context.active_object if context.active_object and context.active_object.type == 'LATTICE' else None
        if not lattice_obj:
            for obj in context.selected_objects:
                if obj.type == 'LATTICE':
                    lattice_obj = obj
                    break
                    
        success, msg = create_armature_for_lattice(context, lattice_obj, only_selected=False)
        if not success:
            self.report({'WARNING'}, msg)
            return {'CANCELLED'}
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class OBJECT_OT_bonify_lattice_selected(bpy.types.Operator):
    bl_idname = "object.bonify_lattice_selected"
    bl_label = "Bonify Selected Lattice Vertices"
    bl_description = "Creates bones for only the selected vertices of the active Lattice"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object and context.active_object.type == 'LATTICE':
            return True
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'LATTICE':
                    return True
        return False

    def execute(self, context):
        lattice_obj = context.active_object if context.active_object and context.active_object.type == 'LATTICE' else None
        if not lattice_obj:
            for obj in context.selected_objects:
                if obj.type == 'LATTICE':
                    lattice_obj = obj
                    break
                    
        success, msg = create_armature_for_lattice(context, lattice_obj, only_selected=True)
        if not success:
            self.report({'WARNING'}, msg)
            return {'CANCELLED'}
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class OBJECT_OT_bonify_lattice_active_bone(bpy.types.Operator):
    bl_idname = "object.bonify_lattice_active_bone"
    bl_label = "Bonify Lattice to Active Bone"
    bl_description = "Creates bones for all vertices of the active Lattice and parents them to the active bone of the selected Armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        has_lattice = False
        has_armature = False
        if context.active_object and context.active_object.type == 'LATTICE':
            has_lattice = True
        elif context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'LATTICE':
                    has_lattice = True
                    break
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    has_armature = True
                    break
        return has_lattice and has_armature

    def execute(self, context):
        lattice_obj = context.active_object if context.active_object and context.active_object.type == 'LATTICE' else None
        if not lattice_obj:
            for obj in context.selected_objects:
                if obj.type == 'LATTICE':
                    lattice_obj = obj
                    break
                    
        success, msg = create_armature_for_lattice(context, lattice_obj, only_selected=False, parent_to_active=True)
        if not success:
            self.report({'WARNING'}, msg)
            return {'CANCELLED'}
        self.report({'INFO'}, msg)
        return {'FINISHED'}


def create_armature_for_mesh(context, mesh_obj, only_selected=False, parent_to_active=False):
    if not mesh_obj or mesh_obj.type != 'MESH':
        return False, "Please select a Mesh object."

    target_vertices = []
    
    current_mode = mesh_obj.mode
    if current_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    mesh = mesh_obj.data
    
    for i, pt in enumerate(mesh.vertices):
        if only_selected:
            if pt.select:
                target_vertices.append((i, pt.co.copy()))
        else:
            target_vertices.append((i, pt.co.copy()))
            
    if not target_vertices:
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=current_mode)
        return False, "No vertices targeted (if 'Selected', ensure vertices are selected in Edit mode)."

    selected_armatures = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']
    
    if selected_armatures:
        arm_obj = selected_armatures[0]
        arm_data = arm_obj.data
    else:
        arm_data = bpy.data.armatures.new(name=f"{mesh_obj.name}_Armature")
        arm_obj = bpy.data.objects.new(name=f"{mesh_obj.name}_Armature", object_data=arm_data)
        context.collection.objects.link(arm_obj)
        
        loc, rot, scale = mesh_obj.matrix_world.decompose()
        arm_obj.matrix_world = mathutils.Matrix.LocRotScale(loc, rot, mathutils.Vector((1.0, 1.0, 1.0)))
    
    bone_col = None
    if hasattr(arm_data, "collections"):
        bone_col = arm_data.collections.get("meshbones")
        if not bone_col:
            bone_col = arm_data.collections.new("meshbones")

    active_bone_name = None
    if parent_to_active and arm_obj.data.bones.active:
        active_bone_name = arm_obj.data.bones.active.name

    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    context.view_layer.objects.active = arm_obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    active_edit_bone = None
    if active_bone_name:
        active_edit_bone = arm_obj.data.edit_bones.get(active_bone_name)

    bone_names = []
    mesh_mat_world = mesh_obj.matrix_world
    arm_mat_inv = arm_obj.matrix_world.inverted()
    
    for idx, co in target_vertices:
        bone_name = f"Bone_{idx}"
        edit_bone = arm_obj.data.edit_bones.new(bone_name)
        bone_name = edit_bone.name
        bone_names.append((idx, bone_name))
        
        world_co = mesh_mat_world @ co
        arm_local_co = arm_mat_inv @ world_co
        
        edit_bone.head = arm_local_co
        edit_bone.tail = arm_local_co + mathutils.Vector((0, 0, 0.5))
        
        if parent_to_active and active_edit_bone:
            edit_bone.parent = active_edit_bone

        if bone_col:
            bone_col.assign(edit_bone)
        
    bpy.ops.object.mode_set(mode='OBJECT')
    
    if mesh_obj.parent != arm_obj:
        mesh_obj.parent = arm_obj
        mesh_obj.parent_type = 'OBJECT'
        mesh_obj.matrix_parent_inverse = arm_obj.matrix_world.inverted()
    
    has_armature_mod = False
    for mod in mesh_obj.modifiers:
        if mod.type == 'ARMATURE' and mod.object == arm_obj:
            has_armature_mod = True
            break
            
    if not has_armature_mod:
        mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
        mod.object = arm_obj
    
    for idx, bone_name in bone_names:
        vg = mesh_obj.vertex_groups.get(bone_name)
        if not vg:
            vg = mesh_obj.vertex_groups.new(name=bone_name)
        vg.add([idx], 1.0, 'REPLACE')

    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    context.view_layer.objects.active = arm_obj
    
    return True, f"Created {len(bone_names)} bones."


class OBJECT_OT_bonify_mesh_all(bpy.types.Operator):
    bl_idname = "object.bonify_mesh_all"
    bl_label = "Bonify All Mesh Vertices"
    bl_description = "Creates bones for all vertices of the active Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object and context.active_object.type == 'MESH':
            return True
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    return True
        return False

    def execute(self, context):
        mesh_obj = context.active_object if context.active_object and context.active_object.type == 'MESH' else None
        if not mesh_obj:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    mesh_obj = obj
                    break
                    
        success, msg = create_armature_for_mesh(context, mesh_obj, only_selected=False)
        if not success:
            self.report({'WARNING'}, msg)
            return {'CANCELLED'}
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class OBJECT_OT_bonify_mesh_selected(bpy.types.Operator):
    bl_idname = "object.bonify_mesh_selected"
    bl_label = "Bonify Selected Mesh Vertices"
    bl_description = "Creates bones for only the selected vertices of the active Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object and context.active_object.type == 'MESH':
            return True
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    return True
        return False

    def execute(self, context):
        mesh_obj = context.active_object if context.active_object and context.active_object.type == 'MESH' else None
        if not mesh_obj:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    mesh_obj = obj
                    break
                    
        success, msg = create_armature_for_mesh(context, mesh_obj, only_selected=True)
        if not success:
            self.report({'WARNING'}, msg)
            return {'CANCELLED'}
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class OBJECT_OT_bonify_mesh_active_bone(bpy.types.Operator):
    bl_idname = "object.bonify_mesh_active_bone"
    bl_label = "Bonify Mesh to Active Bone"
    bl_description = "Creates bones for all vertices of the active Mesh and parents them to the active bone of the selected Armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        has_mesh = False
        has_armature = False
        if context.active_object and context.active_object.type == 'MESH':
            has_mesh = True
        elif context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    has_mesh = True
                    break
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    has_armature = True
                    break
        return has_mesh and has_armature

    def execute(self, context):
        mesh_obj = context.active_object if context.active_object and context.active_object.type == 'MESH' else None
        if not mesh_obj:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    mesh_obj = obj
                    break
                    
        success, msg = create_armature_for_mesh(context, mesh_obj, only_selected=False, parent_to_active=True)
        if not success:
            self.report({'WARNING'}, msg)
            return {'CANCELLED'}
        self.report({'INFO'}, msg)
        return {'FINISHED'}


classes = (
    OBJECT_OT_bonify_lattice_all,
    OBJECT_OT_bonify_lattice_selected,
    OBJECT_OT_bonify_lattice_active_bone,
    OBJECT_OT_bonify_mesh_all,
    OBJECT_OT_bonify_mesh_selected,
    OBJECT_OT_bonify_mesh_active_bone,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
