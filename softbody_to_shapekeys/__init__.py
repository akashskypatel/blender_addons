bl_info = {
    "name": "Bake Soft Body To Shape Keys",
    "author": "Akash Patel",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "location": "Object Right Click Menu",
    "description": "Bake Soft Body cache animation into shape keys",
    "category": "Object",
}

import bpy


def get_soft_body_modifier(obj):
    """
    Get the Soft Body modifier from the given object.
    
    Args:
        obj: The Blender object to check
        
    Returns:
        The Soft Body modifier or None if not found
    """
    if not obj:
        return None

    for mod in obj.modifiers:
        if mod.type == "SOFT_BODY":
            return mod

    return None


def get_frame_range(context, obj=None):
    """
    Get the frame range for the Soft Body simulation.
    
    Args:
        context: The Blender context
        obj: The Blender object to check (optional)
        
    Returns:
        A tuple of (start_frame, end_frame)
    """
    if obj:
        for mod in obj.modifiers:
            if mod.type == "SOFT_BODY" and mod.point_cache:
                return mod.point_cache.frame_start, mod.point_cache.frame_end

    scene = context.scene
    return scene.frame_start, scene.frame_end


def set_shape_key_influence(key, frame, value):
    """
    Set the influence of a shape key at a specific frame.
    
    Args:
        key: The shape key to modify
        frame: The frame number
        value: The influence value (0.0 to 1.0)
    """
    key.value = value
    key.keyframe_insert("value", frame=frame)


def collect_modifiers_after_soft_body(obj, soft_body_mod):
    """
    Collect all modifiers that come after the Soft Body modifier.
    
    Args:
        obj: The Blender object to check
        soft_body_mod: The Soft Body modifier
        
    Returns:
        A list of modifiers that come after the Soft Body modifier
    """
    found_soft_body = False
    modifiers = []

    for mod in obj.modifiers:
        if mod == soft_body_mod:
            found_soft_body = True
            continue

        if found_soft_body:
            modifiers.append(mod)

    return modifiers


def get_evaluated_soft_body_mesh(context, obj, frame, soft_body_mod):
    """
    Get the evaluated mesh for the given object at the specified frame.
    
    Args:
        context: The Blender context
        obj: The Blender object to evaluate
        frame: The frame number
        soft_body_mod: The Soft Body modifier
        
    Returns:
        The evaluated mesh
    """
    disabled_states = []

    # Disable modifiers after Soft Body so Subdivision/etc. does not change vertex count.
    for mod in collect_modifiers_after_soft_body(obj, soft_body_mod):
        disabled_states.append((mod, mod.show_viewport))
        mod.show_viewport = False

    try:
        context.scene.frame_set(frame)
        context.view_layer.update()

        depsgraph = context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)

        return bpy.data.meshes.new_from_object(eval_obj, depsgraph=depsgraph)

    finally:
        for mod, show_viewport in disabled_states:
            mod.show_viewport = show_viewport


def clear_existing_baked_shape_keys(obj, prefix):
    """
    Clear existing shape keys that match the given prefix.
    
    Args:
        obj: The Blender object to clear shape keys from
        prefix: The prefix to match
    """
    if not obj.data.shape_keys:
        return

    for key in list(obj.data.shape_keys.key_blocks):
        if key.name.startswith(prefix):
            obj.shape_key_remove(key)


class OBJECT_OT_bake_soft_body_to_shape_keys(bpy.types.Operator):
    """
    Bake Soft Body simulation to shape keys.
    """
    bl_idname = "object.bake_soft_body_to_shape_keys"
    bl_label = "Bake Soft Body To Shape Keys"
    bl_description = "Bake this Soft Body cache into animated shape keys"
    bl_options = {"REGISTER", "UNDO"}

    frame_start: bpy.props.IntProperty(name="Start Frame", default=1, min=0)
    frame_end: bpy.props.IntProperty(name="End Frame", default=250, min=0)

    key_prefix: bpy.props.StringProperty(
        name="Shape Key Prefix",
        default="SoftBodyFrame_",
    )

    clear_existing: bpy.props.BoolProperty(
        name="Clear Existing Generated Keys",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """
        Check if the operator can be executed.
        
        Args:
            context: The Blender context
            
        Returns:
            True if the operator can be executed, False otherwise
        """
        obj = context.object
        return obj is not None and obj.type == "MESH" and get_soft_body_modifier(obj) is not None

    def invoke(self, context, event):
        """
        Invoke the operator.
        
        Args:
            context: The Blender context
            event: The mouse event
            
        Returns:
            The result of the operator
        """
        self.frame_start, self.frame_end = get_frame_range(context, context.object)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        """
        Execute the operator.
        
        Args:
            context: The Blender context
            
        Returns:
            The result of the operator
        """
        obj = context.object
        soft_body_mod = get_soft_body_modifier(obj)

        if not obj:
            self.report({"ERROR"}, "No active object selected")
            return {"CANCELLED"}

        if obj.type != "MESH":
            self.report({"ERROR"}, "Selected object must be a mesh")
            return {"CANCELLED"}

        if not soft_body_mod:
            self.report({"ERROR"}, "Selected object does not have a Soft Body modifier")
            return {"CANCELLED"}

        if self.frame_end < self.frame_start:
            self.report({"ERROR"}, "End frame must be greater than or equal to start frame")
            return {"CANCELLED"}

        base_vertex_count = len(obj.data.vertices)

        if base_vertex_count == 0:
            self.report({"ERROR"}, "Base mesh has no vertices")
            return {"CANCELLED"}

        original_frame = context.scene.frame_current
        created_count = 0
        skipped_count = 0

        try:
            test_mesh = get_evaluated_soft_body_mesh(
                context,
                obj,
                self.frame_start,
                soft_body_mod,
            )

            try:
                if len(test_mesh.vertices) != base_vertex_count:
                    self.report(
                        {"ERROR"},
                        f"Vertex count mismatch at start frame. "
                        f"Base={base_vertex_count}, evaluated={len(test_mesh.vertices)}. "
                        f"Make sure modifiers before Soft Body do not change topology."
                    )
                    return {"CANCELLED"}
            finally:
                bpy.data.meshes.remove(test_mesh)

            if self.clear_existing:
                clear_existing_baked_shape_keys(obj, self.key_prefix)

            if not obj.data.shape_keys:
                obj.shape_key_add(name="Basis")

            for frame in range(self.frame_start, self.frame_end + 1):
                eval_mesh = get_evaluated_soft_body_mesh(
                    context,
                    obj,
                    frame,
                    soft_body_mod,
                )

                try:
                    if len(eval_mesh.vertices) == 0:
                        skipped_count += 1
                        continue

                    if len(eval_mesh.vertices) != base_vertex_count:
                        self.report(
                            {"ERROR"},
                            f"Topology changed at frame {frame}. "
                            f"Base={base_vertex_count}, evaluated={len(eval_mesh.vertices)}"
                        )
                        return {"CANCELLED"}

                    key = obj.shape_key_add(name=f"{self.key_prefix}{frame:04d}")

                    for i, vert in enumerate(eval_mesh.vertices):
                        key.data[i].co = vert.co

                    set_shape_key_influence(key, frame - 1, 0.0)
                    set_shape_key_influence(key, frame, 1.0)
                    set_shape_key_influence(key, frame + 1, 0.0)

                    created_count += 1
                    print(f"Created shape key {key.name}")

                finally:
                    bpy.data.meshes.remove(eval_mesh)

        except Exception as exc:
            self.report({"ERROR"}, f"Shape key bake failed: {exc}")
            return {"CANCELLED"}

        finally:
            context.scene.frame_set(original_frame)
            context.view_layer.update()

        if created_count == 0:
            self.report({"ERROR"}, "No shape keys were created")
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Created {created_count} shape keys. Skipped {skipped_count} frames"
        )

        return {"FINISHED"}


def draw_soft_body_shape_key_menu(self, context):
    """
    Draw the Soft Body to Shape Keys menu in the object context menu.
    
    Args:
        self: The menu object
        context: The Blender context
    """
    obj = context.object

    if obj and obj.type == "MESH" and get_soft_body_modifier(obj):
        self.layout.separator()
        self.layout.operator(
            OBJECT_OT_bake_soft_body_to_shape_keys.bl_idname,
            icon="SHAPEKEY_DATA",
        )


classes = (
    OBJECT_OT_bake_soft_body_to_shape_keys,
)


def register():
    """
    Register the addon.
    """
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.append(draw_soft_body_shape_key_menu)
    auto_load.register()


def unregister():
    """
    Unregister the addon.
    """
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_soft_body_shape_key_menu)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    auto_load.unregister()


if __name__ == "__main__":
    register()