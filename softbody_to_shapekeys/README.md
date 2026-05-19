# Bake Soft Body To Shape Keys

A Blender addon that bakes Soft Body simulation cache animation into animated shape keys.

**Author:** Akash Patel  
**Version:** 1.1.0  
**Blender:** 3.6.0+  
**License:** [GNU General Public License v3](http://www.gnu.org/licenses/)

---

## Installation

1. Download or clone this repository.
2. In Blender, go to **Edit → Preferences → Add-ons**.
3. Click **Install** and select the `softbody_to_shapekeys` folder (or the zip file).
4. Enable the addon.

## Usage

1. Add a **Soft Body** modifier to a mesh object.
2. Run the simulation to cache the results.
3. Right-click the mesh object and select **Bake Soft Body To Shape Keys**.
4. Adjust the frame range and prefix in the dialog.
5. Click **OK** to bake.

The baked shape keys will use the configured prefix (default: `SoftBodyFrame_`) and animate the influence per frame so the mesh matches the Soft Body simulation at each frame.

## Features

- **Context menu access** — Right-click any mesh with a Soft Body modifier to access the bake operator.
- **Automatic frame range** — Detects the start/end frames from the Soft Body modifier's point cache.
- **Configurable prefix** — Customize the name prefix for generated shape keys (default: `SoftBodyFrame_`).
- **Clear existing keys** — Option to remove previously baked keys before rebaking.
- **Vertex count validation** — Validates that topology remains constant throughout the simulation before baking, with guidance to check modifiers before the Soft Body if validation fails.
- **Modifier isolation** — Disables modifiers below the Soft Body (e.g., Subdivision Surface) during baking to prevent them from changing vertex counts.
- **Preserves Basis** — Always keeps the original mesh as the Basis shape key.
- **Undo support** — All operations can be undone with `Ctrl+Z`.

## Requirements

- **Blender 3.6.0** or newer.

## Limitations

- The mesh **must maintain constant topology** — vertex count and order cannot change between frames. Shape keys require identical vertex counts.
- Modifiers placed **above** the Soft Body modifier in the stack **must not change topology** (e.g., avoid Decimate, Remesh, or Multires above Soft Body). Modifiers below the Soft Body are automatically disabled during baking.
- Currently supports **Soft Body** modifiers only.

## Shortcut

| Action | Location |
|---|---|
| Open bake dialog | Right-click mesh → **Bake Soft Body To Shape Keys** |

## Uninstallation

1. Go to **Edit → Preferences → Add-ons**.
2. Find **Bake Soft Body To Shape Keys**.
3. Click **Remove**.