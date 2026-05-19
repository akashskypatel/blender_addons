# Blender Addons

A collection of Blender addons for converting simulation caches into reusable mesh data.

**Author:** Akash Patel  
**License:** [GNU General Public License v3](http://www.gnu.org/licenses/)

---

## Addons

### [Bake Soft Body To Shape Keys](./softbody_to_shapekeys/) — v1.1.0

Bakes a Soft Body simulation cache into animated shape keys on the mesh itself.

- **Access:** Right-click mesh → **Bake Soft Body To Shape Keys**
- **Blender:** 3.6.0+
- **Requirements:** Mesh with a Soft Body modifier; simulation must be cached
- **Details:** Disables downstream modifiers during bake to keep vertex count stable. Shape keys are animated via keyframed influence values, producing the same visual result as the simulation playback.

---

### [Fluid Cache To Mesh Sequence](./fluid_to_mesh/) — v1.1.0

Converts a baked liquid fluid mesh cache into individual per-frame mesh objects with keyframe-driven visibility.

- **Access:** Right-click fluid domain → **Copy Fluid Cache To Mesh Sequence**
- **Blender:** 3.6.0+ (manifest targets 4.2.0+)
- **Requirements:** Liquid fluid domain; cache type set to Modular or All; both data and mesh caches baked
- **Details:** Each frame becomes a separate mesh object placed in a `{object}_fluid` collection. Meshes are hidden/shown via keyframes so only the correct frame is visible at any given time.

---

## Shared Features

- Access via **Object Right Click Menu** — no need to search through menus.
- **Undo support** — all operations can be reversed with `Ctrl+Z`.
- Automatic **frame range detection** from the simulation's cache settings.
- **Vertex count validation** before baking/exporting to catch topology changes early.
- Built using Blender's standard `auto_load` pattern for clean registration.

---

## Repository Structure

```
blender_addons/
├── README.md                          # This file
├── blender_addons.code-workspace      # VS Code workspace
├── .venv/                             # Python virtual environment
├── softbody_to_shapekeys/             # Addon: Soft Body → Shape Keys
│   ├── __init__.py
│   ├── auto_load.py
│   ├── blender_manifest.toml
│   └── README.md
├── fluid_to_mesh/                     # Addon: Fluid Cache → Mesh Objects
│   ├── __init__.py
│   ├── auto_load.py
│   ├── blender_manifest.toml
│   ├── README.md
│   └── scripts/                       # Standalone helper scripts
│       ├── fluid_cache_to_mesh_sequence.py
│       └── softbody_to_shapekeys.py
```

---

## Installation (per addon)

1. Open the addon folder you want to install.
2. In Blender, go to **Edit → Preferences → Add-ons**.
3. Click **Install** and select the addon's folder (or zip it first).
4. Enable the addon.