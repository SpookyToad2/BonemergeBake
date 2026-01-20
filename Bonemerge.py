bl_info = {
    "name": "Bonemerge with Bake",
    "author": "Herwork, hisanimations",
    "version": (1, 3, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Rigging",
    "description": "Snaps cosmetics to a player rig and bakes animation",
    "warning": "",
    "doc_url": "",
    "category": "Rigging",
}


import bpy
from bpy.types import Operator, Object, Armature
from bpy.props import FloatVectorProperty, EnumProperty, StringProperty, FloatProperty, PointerProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector


loc = "BONEMERGE-ATTACH-LOC"
rot = "BONEMERGE-ATTACH-ROT"

def main(context, mode, targ = None):
    # targ is passed as the name string of the object
    if mode == 0:
        for i in bpy.context.selected_objects:
            if not (i.type == 'MESH' or i.type == 'ARMATURE'):
                continue
            if i.name == targ:
                continue
            if i.type == 'MESH':
                if not i.parent:
                    continue
                else:
                    i = i.parent
            
            for ii in i.pose.bones:
                try:
                    # Check if the target rig has a bone with the same name
                    bpy.data.objects[targ].pose.bones[ii.name]
                except:
                    continue
                    
                try:
                    ii.constraints[loc]
                    pass
                except:
                    ii.constraints.new('COPY_LOCATION').name = loc
                    ii.constraints.new('COPY_ROTATION').name = rot
                
                ii.constraints[loc].target = bpy.data.objects[targ]
                ii.constraints[loc].subtarget = ii.name
                ii.constraints[rot].target = bpy.data.objects[targ]
                ii.constraints[rot].subtarget = ii.name

    if mode == 1:
        for i in bpy.context.selected_objects:
            if not (i.type == 'MESH' or i.type == 'ARMATURE'):
                continue
            if i.type == 'MESH':
                if not i.parent:
                    continue
                else:
                    i = i.parent
            for ii in i.pose.bones:
                try:
                    ii.constraints.remove(ii.constraints[loc])
                    ii.constraints.remove(ii.constraints[rot])
                except:
                    continue


class addArm(bpy.types.Operator):
    """Attach cosmetics"""
    bl_idname = "rig.snap"
    bl_label = "Attach"
    bl_options = {'UNDO'} 
    
    def execute(self, context):
        scene = context.scene
        targ = scene.mychosenObject
        if targ == None:
            self.report({"ERROR"}, "No player rig found")
            return {'CANCELLED'}
        
        try:
            main(context, 0, targ.name)
            return {'FINISHED'}
        except Exception as e:
            self.report({"ERROR"}, f"Error attaching: {str(e)}")
            return {'CANCELLED'}


class removeArm(bpy.types.Operator):
    """Detach cosmetics"""
    bl_idname = "rig.remove"
    bl_label = "Detach"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        try:
            main(context, 1) # Target is not needed for removal
            return {'FINISHED'}
        except Exception as e:
            self.report({"ERROR"}, f"Error detaching: {str(e)}")
            return {'CANCELLED'}


class bakeArm(bpy.types.Operator):
    """Bake animation to the selected armature and remove constraints"""
    bl_idname = "rig.bake"
    bl_label = "Bake Animation"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        
        # Check if we have selected armatures
        selected_armatures = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']
        
        if not selected_armatures:
            self.report({"ERROR"}, "Please select the target armature (arms02) to bake.")
            return {'CANCELLED'}

        # Bake settings
        frame_start = scene.frame_start
        frame_end = scene.frame_end
        
        for obj in selected_armatures:
            try:
                # 1. Set object as active
                context.view_layer.objects.active = obj
                
                # 2. Enter Pose Mode
                bpy.ops.object.mode_set(mode='POSE')
                
                # 3. Select all bones to ensure everything gets baked
                bpy.ops.pose.select_all(action='SELECT')
                
                # 4. Bake
                # visual_keying=True: Captures the movement from the constraints
                # clear_constraints=True: Removes the 'Attach' constraints after baking
                bpy.ops.nla.bake(
                    frame_start=frame_start,
                    frame_end=frame_end,
                    visual_keying=True,
                    only_selected=True,
                    use_current_action=True,
                    clear_constraints=True,
                    bake_types={'POSE'}
                )
                
                # 5. Return to Object Mode
                bpy.ops.object.mode_set(mode='OBJECT')
                
            except Exception as e:
                self.report({"ERROR"}, f"Failed to bake {obj.name}: {str(e)}")
                return {'CANCELLED'}

        self.report({"INFO"}, "Animation baked and constraints removed.")
        return {'FINISHED'}


class TestPanel(bpy.types.Panel):
    bl_label = "Bonemerge"
    bl_idname = "PT_MergePanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bonemerge"
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        
        col = layout.column()
        col.label(text= "Select the player rig", icon= "RESTRICT_SELECT_OFF")
        col.prop(scene, "mychosenObject", text="", expand=True)
        
        layout.separator()
        
        col = layout.column(align=True)
        col.label(text= "Actions", icon= "COMMUNITY")
        
        row = col.row(align=True)
        row.operator("rig.snap", icon="LINKED")
        row.operator("rig.remove", icon="UNLINKED")
        
        col.separator()
        col.operator("rig.bake", icon="ACTION", text="Bake Animation")


# Registration

def poll_armature(self, object):
    return object.type == 'ARMATURE'

classes = [TestPanel, addArm, removeArm, bakeArm]        
        
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Updated to proper Object type for Blender 2.8+ compatibility
    bpy.types.Scene.mychosenObject = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=poll_armature,
        name="Target Rig",
        description="The source armature (e.g. arms01) with the animation"
    )
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.mychosenObject
    
if __name__ == "__main__":
    register()