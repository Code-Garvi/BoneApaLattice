import bpy
import mathutils

def create_armature_for_lattice(context, lattice_obj, only_selected=False):
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

    arm_data = bpy.data.armatures.new(name=f"{lattice_obj.name}_Armature")
    arm_obj = bpy.data.objects.new(name=f"{lattice_obj.name}_Armature", object_data=arm_data)
    
    context.collection.objects.link(arm_obj)
    
    # 1. Strip scaling from the Armature.
    # Non-uniform scales on Armature objects cause massive skewing bugs in Blender.
    # We copy only the location and rotation from the lattice.
    loc, rot, scale = lattice_obj.matrix_world.decompose()
    arm_obj.matrix_world = mathutils.Matrix.LocRotScale(loc, rot, mathutils.Vector((1.0, 1.0, 1.0)))
    
    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    context.view_layer.objects.active = arm_obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    bone_names = []
    lattice_mat_world = lattice_obj.matrix_world
    arm_mat_inv = arm_obj.matrix_world.inverted()
    
    for idx, co in target_vertices:
        bone_name = f"Bone_{idx}"
        bone_names.append((idx, bone_name))
        
        edit_bone = arm_obj.data.edit_bones.new(bone_name)
        
        # 2. Perfect spatial alignment
        # We transform the vertex coordinate (which is in Lattice local space) into World space.
        # Then, we transform it from World space into the Armature's unscaled local space.
        world_co = lattice_mat_world @ co
        arm_local_co = arm_mat_inv @ world_co
        
        edit_bone.head = arm_local_co
        # Add a slight tail thickness for usability
        edit_bone.tail = arm_local_co + mathutils.Vector((0, 0, 0.5))
        
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 3. Pure API Parenting to avoid operator context errors
    # We set the parent seamlessly by providing the exact inverse world matrix of the armature.
    lattice_obj.parent = arm_obj
    lattice_obj.matrix_parent_inverse = arm_obj.matrix_world.inverted()
    
    # 4. Bind the armature correctly
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
    bl_label = "Bonify All Vertices"
    bl_description = "Creates bones for all vertices of the active Lattice"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'LATTICE'

    def execute(self, context):
        success, msg = create_armature_for_lattice(context, context.active_object, only_selected=False)
        if not success:
            self.report({'WARNING'}, msg)
            return {'CANCELLED'}
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class OBJECT_OT_bonify_lattice_selected(bpy.types.Operator):
    bl_idname = "object.bonify_lattice_selected"
    bl_label = "Bonify Selected Vertices"
    bl_description = "Creates bones for only the selected vertices of the active Lattice"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'LATTICE'

    def execute(self, context):
        success, msg = create_armature_for_lattice(context, context.active_object, only_selected=True)
        if not success:
            self.report({'WARNING'}, msg)
            return {'CANCELLED'}
        self.report({'INFO'}, msg)
        return {'FINISHED'}


classes = (
    OBJECT_OT_bonify_lattice_all,
    OBJECT_OT_bonify_lattice_selected,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
