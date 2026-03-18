import bpy

class VIEW3D_PT_bonify_lattice_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoneApaLattice'
    bl_label = 'BoneApaLattice'

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        col.label(text="Lattice Operations:")
        col.operator("object.bonify_lattice_all", text="Bonify All Lattice Vertices")
        col.operator("object.bonify_lattice_selected", text="Bonify Selected Lattice Vertices")
        col.operator("object.bonify_lattice_active_bone", text="Bonify Lattice to Active Bone")
        
        col.separator()
        
        col.label(text="Mesh Operations:")
        col.operator("object.bonify_mesh_all", text="Bonify All Mesh Vertices")
        col.operator("object.bonify_mesh_selected", text="Bonify Selected Mesh Vertices")
        col.operator("object.bonify_mesh_active_bone", text="Bonify Mesh to Active Bone")

classes = (
    VIEW3D_PT_bonify_lattice_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
