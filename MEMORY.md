# Memory: BoneApaLattice Dev Continuation

## Project Overview
BoneApaLattice is a Blender add-on for Blender 4.2+ that creates an armature matching the vertices of a selected Lattice or Mesh, wiring up 1:1 vertex weight groups so each vertex is controllable via a bone.

## Environment & Blender Setup
- **Target Blender**: Portable Blender 4.5.8 (`E:\Blender\Portable_Blender\blender-4.5.8-windows-x64\blender.exe`).
- **Addon Junction**: `E:\Blender\Portable_Blender\blender-4.5.8-windows-x64\portable\scripts\addons\boneapalattice` linked to `E:\Github Projects\BonApaLattice Dev Continuation`.
- **Blender MCP Server**: Available via `bl_ext.user_default.mcp` running on `localhost:9876`.
- **Archive**: `archive/boneapalattice.zip` preserved locally, ignored by `.gitignore`.

## Branches & Git State
- **`development`**: Active working branch. Contains latest code from zip with version 1.0.0, `.gitignore`, full lattice & mesh operations, media assets. Pushed to `origin/development`.
- **`main`**: Cleanly merged with `development` and pushed to `origin/main`.

## Current Features
1. **Lattice Operations**:
   - `object.bonify_lattice_all`: Generates bones for all points in lattice.
   - `object.bonify_lattice_selected`: Generates bones for only selected points in lattice.
   - `object.bonify_lattice_active_bone`: Parents created lattice bones under active bone of selected armature.
2. **Mesh Operations**:
   - `object.bonify_mesh_all`: Generates bones for all mesh vertices.
   - `object.bonify_mesh_selected`: Generates bones for only selected mesh vertices.
   - `object.bonify_mesh_active_bone`: Parents created mesh bones under active bone of selected armature.
3. **Blender 4.0+ Collections**: Bones placed in `latticebones` or `meshbones` collections.

## Next Immediate Step
- Confirm next feature, enhancement, or test to implement with the user.
