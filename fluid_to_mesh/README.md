# Fluid Cache To Mesh Sequence

A Blender addon that converts a baked liquid fluid mesh cache into per-frame mesh objects, with keyframe-driven visibility for smooth playback in the viewport and renders.

**Author:** Akash Patel  
**Version:** 1.1.0  
**Blender:** 3.6.0+  
**License:** [GNU General Public License v3](http://www.gnu.org/licenses/)

---

## Installation

1. Download or clone this repository.
2. In Blender, go to **Edit → Preferences → Add-ons**.
3. Click **Install** and select the `fluid_to_mesh` folder (or the zip file).
4. Enable the addon.

## Usage

1. Set up a **Fluid** domain with **Type: Liquid** on a mesh object.
2. In the domain's cache settings, set **Cache Type** to **Modular** or **All** (not **Replay**).
3. Enable **Mesh** under the liquid domain settings.
4. **Bake** both the fluid data and the fluid mesh cache.
5. Right-click the domain object and select **Copy Fluid Cache To Mesh Sequence**.
6. A collection named `{object_name}_fluid` will be created, containing one mesh per cached frame. Each mesh is keyframed to appear only on its corresponding frame.

## Features

- **Context menu access** — Right-click any fluid domain object to access the export operator.
- **Automatic frame range** — Uses the fluid domain's baked cache frame range.
- **Dedicated collection** — All generated meshes are placed in a `{object}_fluid` collection, keeping the scene organized.
- **Keyframe animation** — Each mesh is animated to show only on its specific frame using `hide_viewport` and `hide_render` keyframes, making it ready for playback or rendering.
- **Vertex validation** — Skips and reports empty frames before creating objects.
- **Auto-enables mesh** — Prompts to enable liquid mesh generation if it was not already active.
- **Undo support** — All operations can be undone with `Ctrl+Z`.

## Requirements

- **Blender 3.6.0** or newer.
- A **Liquid** fluid domain (not gas/smoke).
- **Cache Type** must be **Modular** or **All** (not **Replay**).
- Both the fluid **Data** and **Mesh** caches must be baked before running.

## Limitations

- Only **Liquid** fluid domains are supported. Gas/smoke domains are not supported.
- The fluid mesh cache **must be baked** before running the operator. See the error messages for guidance if the cache is missing.
- Each generated mesh is a standalone object — the sequence is not automatically connected to the original domain.

## Shortcut

| Action | Location |
|---|---|
| Export fluid cache | Right-click fluid domain → **Copy Fluid Cache To Mesh Sequence** |

## Uninstallation

1. Go to **Edit → Preferences → Add-ons**.
2. Find **Fluid Cache To Mesh Sequence**.
3. Click **Remove**.