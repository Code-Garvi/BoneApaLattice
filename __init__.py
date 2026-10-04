bl_info = {
    "name": "BoneApaLattice",
    "author": "Garvi",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > Bonify",
    "description": "Creates an armature matching the vertices of a selected Lattice",
    "warning": "",
    "doc_url": "",
    "category": "Rigging",
}

import bpy
from . import operator
from . import panel

modules = [
    operator,
    panel,
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register()
