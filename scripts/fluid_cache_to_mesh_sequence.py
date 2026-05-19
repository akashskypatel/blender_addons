bl_info = {
    "name": "Fluid Cache To Mesh Sequence",
    "author": "Akash Patel",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "location": "Object Right Click Menu",
    "description": "Convert a baked liquid fluid mesh cache into per-frame mesh objects",
    "category": "Object",
}

import bpy


def get_fluid_domain_modifier(obj):
    if not obj:
        return None

    for mod in obj.modifiers:
        if mod.type == "FLUID" and mod.fluid_type == "DOMAIN":
            return mod

    return None


def evaluated_mesh_vertex_count(context, domain_obj, frame):
    scene = context.scene
    scene.frame_set(frame)
    context.view_layer.update()

    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = domain_obj.evaluated_get(depsgraph)

    mesh = bpy.data.meshes.new_from_object(eval_obj, depsgraph=depsgraph)

    try:
        return len(mesh.vertices)
    finally:
        bpy.data.meshes.remove(mesh)


class OBJECT_OT_fluid_cache_to_mesh_sequence(bpy.types.Operator):
    bl_idname = "object.fluid_cache_to_mesh_sequence"
    bl_label = "Copy Fluid Cache To Mesh Sequence"
    bl_description = "Copy this baked liquid fluid mesh cache into per-frame mesh objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_fluid_domain_modifier(context.object) is not None

    def execute(self, context):
        domain_obj = context.object

        if not domain_obj:
            self.report({"ERROR"}, "No active object selected")
            return {"CANCELLED"}

        fluid_mod = get_fluid_domain_modifier(domain_obj)

        if not fluid_mod:
            self.report({"ERROR"}, "Selected object does not have a fluid domain modifier")
            return {"CANCELLED"}

        domain = fluid_mod.domain_settings

        if not domain:
            self.report({"ERROR"}, "Fluid domain settings not available")
            return {"CANCELLED"}

        if domain.domain_type != "LIQUID":
            self.report({"ERROR"}, "Fluid domain must be LIQUID to export mesh cache")
            return {"CANCELLED"}

        if domain.cache_frame_end < domain.cache_frame_start:
            self.report({"ERROR"}, "Invalid cache frame range")
            return {"CANCELLED"}

        if domain.cache_type == "REPLAY":
            self.report({"ERROR"}, "Cache type is REPLAY. Use MODULAR or ALL and bake the cache first")
            return {"CANCELLED"}

        if not domain.use_mesh:
            domain.use_mesh = True
            self.report({"WARNING"}, "Enabled liquid mesh generation. Bake the mesh cache, then run again")
            return {"CANCELLED"}

        if hasattr(domain, "is_cache_baking_any") and domain.is_cache_baking_any:
            self.report({"ERROR"}, "Fluid cache is currently baking. Wait for it to finish, then run again")
            return {"CANCELLED"}

        if hasattr(domain, "has_cache_baked_data") and not domain.has_cache_baked_data:
            self.report({"ERROR"}, "Fluid data cache is not baked. Bake fluid data first")
            return {"CANCELLED"}

        if hasattr(domain, "has_cache_baked_mesh") and not domain.has_cache_baked_mesh:
            self.report({"ERROR"}, "Fluid mesh cache is not baked. Bake fluid mesh first")
            return {"CANCELLED"}

        start_frame = domain.cache_frame_start
        end_frame = domain.cache_frame_end
        original_frame = context.scene.frame_current

        # Test first valid frame before generating objects.
        try:
            first_count = evaluated_mesh_vertex_count(context, domain_obj, start_frame)
        except Exception as exc:
            context.scene.frame_set(original_frame)
            self.report({"ERROR"}, f"Could not evaluate fluid mesh: {exc}")
            return {"CANCELLED"}

        if first_count == 0:
            context.scene.frame_set(original_frame)
            self.report(
                {"ERROR"},
                "Evaluated mesh is empty at the first cache frame. Check that the liquid mesh cache is baked"
            )
            return {"CANCELLED"}

        object_name = domain_obj.name
        collection_name = f"{object_name}_fluid"

        new_collection = bpy.data.collections.get(collection_name)

        if not new_collection:
            new_collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(new_collection)

        depsgraph = context.evaluated_depsgraph_get()
        created_count = 0
        skipped_count = 0

        try:
            for frame in range(start_frame, end_frame + 1):
                context.scene.frame_set(frame)
                context.view_layer.update()

                eval_obj = domain_obj.evaluated_get(depsgraph)

                mesh = bpy.data.meshes.new_from_object(
                    eval_obj,
                    depsgraph=depsgraph
                )

                if len(mesh.vertices) == 0:
                    bpy.data.meshes.remove(mesh)
                    skipped_count += 1
                    print(f"Skipped frame {frame}: empty mesh")
                    continue

                new_obj = bpy.data.objects.new(
                    f"{object_name}_fluid_{frame:04d}",
                    mesh
                )

                new_collection.objects.link(new_obj)
                new_obj.matrix_world = domain_obj.matrix_world.copy()

                # Hidden before frame
                new_obj.hide_viewport = True
                new_obj.hide_render = True
                new_obj.keyframe_insert("hide_viewport", frame=frame - 1)
                new_obj.keyframe_insert("hide_render", frame=frame - 1)

                # Visible on frame
                new_obj.hide_viewport = False
                new_obj.hide_render = False
                new_obj.keyframe_insert("hide_viewport", frame=frame)
                new_obj.keyframe_insert("hide_render", frame=frame)

                # Hidden after frame
                new_obj.hide_viewport = True
                new_obj.hide_render = True
                new_obj.keyframe_insert("hide_viewport", frame=frame + 1)
                new_obj.keyframe_insert("hide_render", frame=frame + 1)

                created_count += 1
                print(f"Created {new_obj.name}")

        except Exception as exc:
            self.report({"ERROR"}, f"Export failed: {exc}")
            return {"CANCELLED"}

        finally:
            context.scene.frame_set(original_frame)
            context.view_layer.update()

        if created_count == 0:
            self.report({"ERROR"}, "No mesh objects were created. Every evaluated frame was empty")
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Created {created_count} mesh objects. Skipped {skipped_count} empty frames"
        )

        return {"FINISHED"}


def draw_fluid_cache_menu(self, context):
    if get_fluid_domain_modifier(context.object):
        self.layout.separator()
        self.layout.operator(
            OBJECT_OT_fluid_cache_to_mesh_sequence.bl_idname,
            icon="MOD_FLUIDSIM"
        )


classes = (
    OBJECT_OT_fluid_cache_to_mesh_sequence,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.append(draw_fluid_cache_menu)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_fluid_cache_menu)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()