bl_info = {
    "name": "Bake Simulation To Shape Keys",
    "author": "Akash Patel",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "Object Right Click Menu",
    "description": "Bake constant-topology evaluated mesh animation, such as soft body, into shape keys",
    "category": "Object",
}

import bpy


def has_soft_body_modifier(obj):
    """
    Check if the object has a soft body modifier.
    
    Args:
        obj: The object to check
        
    Returns:
        bool: True if the object has a soft body modifier, False otherwise
    """
    if not obj:
        return False

    return any(mod.type == "SOFT_BODY" for mod in obj.modifiers)


def get_frame_range(context):
    """
    Get the frame range from the scene.
    
    Args:
        context: The Blender context
        
    Returns:
        tuple: The start and end frame of the scene
    """
    scene = context.scene
    return scene.frame_start, scene.frame_end


def get_evaluated_mesh(context, obj, frame):
    """
    Get the evaluated mesh for a given frame.
    
    Args:
        context: The Blender context
        obj: The object to evaluate
        frame: The frame to evaluate
        
    Returns:
        bpy.types.Mesh: The evaluated mesh
    """
    scene = context.scene
    scene.frame_set(frame)
    context.view_layer.update()

    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)

    return bpy.data.meshes.new_from_object(eval_obj, depsgraph=depsgraph)


def clear_existing_baked_shape_keys(obj, prefix="SimFrame_"):
    """
    Clear existing baked shape keys from the object.
    
    Args:
        obj: The object to clear shape keys from
        prefix: The prefix of the shape keys to clear
    """
    if not obj.data.shape_keys:
        return

    keys = obj.data.shape_keys.key_blocks

    # Remove generated frame keys only, preserve Basis and user keys.
    for key in list(keys):
        if key.name.startswith(prefix):
            obj.shape_key_remove(key)


def set_shape_key_influence(key, frame, value):
    """
    Set the influence of a shape key at a given frame.
    
    Args:
        key: The shape key to set
        frame: The frame to set the influence at
        value: The influence value to set
    """
    key.value = value
    key.keyframe_insert("value", frame=frame)


class OBJECT_OT_bake_simulation_to_shape_keys(bpy.types.Operator):
    """
    Bake simulation to shape keys operator.
    """
    bl_idname = "object.bake_simulation_to_shape_keys"
    bl_label = "Bake Simulation To Shape Keys"
    bl_description = "Bake this constant-topology simulation into animated shape keys"
    bl_options = {"REGISTER", "UNDO"}

    frame_start: bpy.props.IntProperty(
        name="Start Frame",
        default=1,
        min=0,
    )

    frame_end: bpy.props.IntProperty(
        name="End Frame",
        default=250,
        min=0,
    )

    key_prefix: bpy.props.StringProperty(
        name="Shape Key Prefix",
        default="SimFrame_",
    )

    clear_existing: bpy.props.BoolProperty(
        name="Clear Existing Generated Keys",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (
            obj is not None
            and obj.type == "MESH"
            and has_soft_body_modifier(obj)
        )

    def invoke(self, context, event):
        """
        Invoke the operator and show the properties dialog.
        
        Args:
            context: The Blender context
            event: The mouse event
            
        Returns:
            set: The return value
        """
        self.frame_start, self.frame_end = get_frame_range(context)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        """
        Execute the operator.
        
        Args:
            context: The Blender context
            
        Returns:
            set: The return value
        """
        obj = context.object

        if not obj:
            self.report({"ERROR"}, "No active object selected")
            return {"CANCELLED"}

        if obj.type != "MESH":
            self.report({"ERROR"}, "Selected object must be a mesh")
            return {"CANCELLED"}

        if not has_soft_body_modifier(obj):
            self.report({"ERROR"}, "Selected object does not have a Soft Body modifier")
            return {"CANCELLED"}

        if self.frame_end < self.frame_start:
            self.report({"ERROR"}, "End frame must be greater than or equal to start frame")
            return {"CANCELLED"}

        original_frame = context.scene.frame_current
        base_vertex_count = len(obj.data.vertices)

        if base_vertex_count == 0:
            self.report({"ERROR"}, "Object has no vertices")
            return {"CANCELLED"}

        try:
            test_mesh = get_evaluated_mesh(context, obj, self.frame_start)
            test_vertex_count = len(test_mesh.vertices)
            bpy.data.meshes.remove(test_mesh)
        except Exception as exc:
            context.scene.frame_set(original_frame)
            self.report({"ERROR"}, f"Could not evaluate mesh: {exc}")
            return {"CANCELLED"}

        if test_vertex_count == 0:
            context.scene.frame_set(original_frame)
            self.report({"ERROR"}, "Evaluated mesh is empty at the start frame")
            return {"CANCELLED"}

        if test_vertex_count != base_vertex_count:
            context.scene.frame_set(original_frame)
            self.report(
                {"ERROR"},
                f"Vertex count mismatch at start frame. Base={base_vertex_count}, Evaluated={test_vertex_count}"
            )
            return {"CANCELLED"}

        if self.clear_existing:
            clear_existing_baked_shape_keys(obj, self.key_prefix)

        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis")

        created_count = 0
        skipped_count = 0

        try:
            for frame in range(self.frame_start, self.frame_end + 1):
                eval_mesh = get_evaluated_mesh(context, obj, frame)

                try:
                    if len(eval_mesh.vertices) == 0:
                        skipped_count += 1
                        print(f"Skipped frame {frame}: empty evaluated mesh")
                        continue

                    if len(eval_mesh.vertices) != base_vertex_count:
                        self.report(
                            {"ERROR"},
                            f"Topology changed at frame {frame}. Shape keys require identical vertex counts"
                        )
                        return {"CANCELLED"}

                    key = obj.shape_key_add(name=f"{self.key_prefix}{frame:04d}")

                    for i, vert in enumerate(eval_mesh.vertices):
                        key.data[i].co = vert.co

                    # Hidden before frame
                    set_shape_key_influence(key, frame - 1, 0.0)

                    # Active on this frame
                    set_shape_key_influence(key, frame, 1.0)

                    # Hidden after frame
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
    Draw the soft body shape key menu in the object context menu.
    
    Args:
        self: The menu object
        context: The Blender context
    """
    obj = context.object

    if obj and obj.type == "MESH" and has_soft_body_modifier(obj):
        self.layout.separator()
        self.layout.operator(
            OBJECT_OT_bake_simulation_to_shape_keys.bl_idname,
            icon="SHAPEKEY_DATA"
        )


classes = (
    OBJECT_OT_bake_simulation_to_shape_keys,
)


def register():
    """
    Register the addon classes.
    """
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.append(draw_soft_body_shape_key_menu)


def unregister():
    """
    Unregister the addon classes.
    """
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_soft_body_shape_key_menu)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()