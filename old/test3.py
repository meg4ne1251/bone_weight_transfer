import bpy

class VertexGroupSelectorOperator(bpy.types.Operator):
    bl_idname = "object.vertex_group_selector"
    bl_label = "Save Vertex Group Info"
    
    def execute(self, context):
        # Get the selected vertex group name
        obj = context.object
        vertex_group_name = context.scene.vertex_group_name

        # Check if the object has the vertex group
        if obj and vertex_group_name in obj.vertex_groups:
            # Write the vertex group info to a text file
            file_path = bpy.path.abspath("//vertex_group_info.txt")
            with open(file_path, 'w') as file:
                file.write(f"Vertex Group Name: {vertex_group_name}\n")
                vertex_group = obj.vertex_groups[vertex_group_name]
                for vertex in obj.data.vertices:
                    group_weight = vertex.group_weights.get(vertex_group.index, 0.0)
                    file.write(f"Vertex {vertex.index}: Weight = {group_weight}\n")
            self.report({'INFO'}, f"Vertex group info saved to {file_path}")
        else:
            self.report({'ERROR'}, "Selected vertex group not found in the active object")
        
        return {'FINISHED'}

class VertexGroupSelectorPanel(bpy.types.Panel):
    bl_label = "Vertex Group Selector"
    bl_idname = "OBJECT_PT_vertex_group_selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    def draw(self, context):
        layout = self.layout
        
        # Create a dropdown for vertex group selection
        obj = context.object
        if obj and obj.type == 'MESH':
            vertex_groups = obj.vertex_groups
            vertex_group_names = [vg.name for vg in vertex_groups]
            layout.prop(context.scene, "vertex_group_name", text="Vertex Group")
            
            # Add a button to execute the operator
            layout.operator("object.vertex_group_selector")
        else:
            layout.label(text="No mesh object selected")

def register():
    bpy.utils.register_class(VertexGroupSelectorOperator)
    bpy.utils.register_class(VertexGroupSelectorPanel)
    
    # Create a new string property to hold the selected vertex group name
    bpy.types.Scene.vertex_group_name = bpy.props.StringProperty(
        name="Vertex Group",
        description="Name of the selected vertex group",
        default=""
    )

def unregister():
    bpy.utils.unregister_class(VertexGroupSelectorOperator)
    bpy.utils.unregister_class(VertexGroupSelectorPanel)
    
    # Remove the string property
    del bpy.types.Scene.vertex_group_name

if __name__ == "__main__":
    register()
