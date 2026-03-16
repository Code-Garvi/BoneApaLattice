import bpy

class VIEW3D_PT_bonify_lattice_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoneApaLattice'
    bl_label = 'BoneApaLattice'

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("object.bonify_lattice_all", text="Bonify All Vertices")
        col.operator("object.bonify_lattice_selected", text="Bonify Selected Vertices")

classes = (
    VIEW3D_PT_bonify_lattice_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
