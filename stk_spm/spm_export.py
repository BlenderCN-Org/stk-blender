#!BPY

"""
Name: 'SPM Exporter (.spm)...'
Blender: 262
Group: 'Export'
Tooltip: 'Export to space paritioned mesh file format (.spm)'
"""

__version__ = "1.0"
__bpydoc__ = """\
"""

bl_info = {
    "name": "SPM (Space paritioned mesh) Model Exporter",
    "description": "Exports a blender scene or object to the SPM format",
    "version": (1,0),
    "blender": (2, 6, 2),
    "api": 31236,
    "location": "File > Export",
    "category": "Import-Export"}

import bpy
import sys,os,os.path,struct,math,string
import mathutils
import math
from subprocess import call

spm_parameters = {}
the_scene = None

# Axis conversion
axis_conversion = mathutils.Matrix([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])

# Helper Functions
def write3Float(value1, value2, value3):
    return struct.pack("<fff", value1, value2, value3)

def write4Float(value1, value2, value3, value4):
    return struct.pack("<ffff", value1, value2, value3, value4)

def writeFloat(value1):
    return struct.pack("<f", value1)

def writeInt(value1):
    return struct.pack("<i", value1)

def writeMatrixAsLocRotScale(mat):
    loc, rot, scale = mat.decompose()
    loc = loc.to_tuple()
    rot = (-rot.x, -rot.z, -rot.y, rot.w)
    scale = scale.to_tuple()
    return struct.pack('<ffffffffff', loc[0], loc[2], loc[1], rot[0], rot[1], rot[2], rot[3], scale[0], scale[2], scale[1])

def writeString(value):
    encoded = str.encode(value)
    if len(encoded) > 64:
        value = encoded[0:64]
    binary_format = "<%ds" % 64
    return struct.pack(binary_format, encoded)

def getUniqueFrame(armature):
    unique_frame = []
    if armature.animation_data.action:
        ipo = armature.animation_data.action.fcurves
        for curve in ipo:
            if "pose" in curve.data_path:
                for keyframe in curve.keyframe_points:
                    if keyframe.co[0] < 0:
                        continue
                    global_key = int(keyframe.co[0])
                    global_key = 1 if global_key is 0 else global_key
                    if not global_key in unique_frame:
                        unique_frame.append(global_key)

    for nla_track in armature.animation_data.nla_tracks:
        for nla_strip in nla_track.strips:
            max_frame = int(nla_track.strips[-1].frame_end)
            if nla_strip.action:
                for action_group in nla_strip.action.groups:
                    for curve in action_group.channels:
                        for keyframe in curve.keyframe_points:
                            if keyframe.co[0] < 0:
                                continue
                            global_key = int(nla_strip.frame_start + keyframe.co[0])
                            if global_key > max_frame:
                                global_key = int(nla_strip.frame_start)
                            global_key = 1 if global_key is 0 else global_key
                            #print('f: {} {} {}'.format(nla_strip.name, nla_strip.frame_start, keyframe.co[0]))
                            if not global_key in unique_frame:
                                unique_frame.append(global_key)

    for pose_bone in armature.pose.bones:
        for constraint in pose_bone.constraints:
            try:
                if constraint.target.animation_data.action:
                    ipo = constraint.target.animation_data.action.fcurves
                    for curve in ipo:
                        for modifier in curve.modifiers:
                            if modifier.frame_start > 0 and modifier.frame_end > 0:
                                for f in range(int(modifier.frame_start), int(modifier.frame_end + 1)):
                                    #print('{} {}'.format(f, modifier.type))
                                    if not f in unique_frame:
                                        unique_frame.append(f)
                        #print('{}'.format(constraint.name))
                        for keyframe in curve.keyframe_points:
                            if keyframe.co[0] < 0:
                                continue
                            global_key = int(keyframe.co[0])
                            global_key = 1 if global_key is 0 else global_key
                            #print('f: {} {}'.format(global_key, constraint.target.name))
                            if not global_key in unique_frame:
                                unique_frame.append(global_key)
            except (AttributeError) as e:
                pass

    unique_frame.sort()
    #for frame in unique_frame:
    #    print('unique_frame:{} {}'.format(frame, armature.name))
    if spm_parameters.get("keyframes-only") is False:
        first = bpy.context.scene.frame_start
        last = unique_frame[-1]
        unique_frame = []
        for frame in range(first, last + 1):
            unique_frame.append(frame)
        #for frame in unique_frame:
        #    print('unique_frame:{} {}'.format(frame, armature.name))
    return unique_frame

# ==== Write SPM File ====
# (main exporter function)
def writeSPMFile(filename, objects=[]):

    import time
    start = time.time()
    if objects:
        exp_obj = objects
    else:
        if spm_parameters.get("export-selected"):
            exp_obj = [ob for ob in bpy.data.objects if ob.select]
        else:
            exp_obj = bpy.data.objects

    buf = bytearray()
    joint_buf = bytearray()
    arm_count = 0
    accumulated_bone = 0
    arm_dict = {}

    static_mesh_frame = spm_parameters.get("static-mesh-frame") if spm_parameters.get("static-mesh-frame") > 0 else bpy.context.scene.frame_start
    for obj in exp_obj:
        if obj.type != "MESH":
            continue

        arm = obj.find_armature()
        if arm != None and not arm in arm_dict:
            animated_buf = bytearray()
            animated_buf += writeString(arm.data.name)
            animated_buf += writeInt(static_mesh_frame)
            animated_buf += writeInt(len(arm.data.bones))

            for group in arm.data.bones:
                bone = arm.data.bones[group.name]
                animated_buf += writeString(group.name)
                animated_buf += writeMatrixAsLocRotScale(bone.matrix_local.inverted())

            unique_frame = getUniqueFrame(arm)
            animated_buf += writeInt(len(unique_frame))
            for frame in unique_frame:
                animated_buf += writeInt(frame - 1)
                animated_buf += writeInt(len(arm.pose.bones))
                bpy.context.scene.frame_set(frame)
                for pose_bone in arm.pose.bones:
                    if pose_bone.parent:
                        bone_mat = pose_bone.parent.matrix.inverted() * pose_bone.matrix
                        pname = pose_bone.parent.name
                    else:
                        if spm_parameters.get("local-space"):
                            bone_mat = pose_bone.matrix.copy()
                        else:
                            bone_mat = arm.matrix_world * pose_bone.matrix.copy()
                        pname = "NULL"
                    animated_buf += writeString(pose_bone.name)
                    animated_buf += writeString(pname)
                    animated_buf += writeMatrixAsLocRotScale(bone_mat)
            mat_data = open(filename + str(arm_count) + ".animated_data",'wb')
            mat_data.write(animated_buf)
            mat_data.close()
            arm_count = arm_count + 1
            arm_dict[arm] = accumulated_bone
            accumulated_bone = accumulated_bone + len(arm.pose.bones)

        bpy.context.scene.frame_set(static_mesh_frame)
        if spm_parameters.get("apply-modifiers"):
            mesh = obj.to_mesh(the_scene, True, 'PREVIEW')
        else:
            mesh = obj.data
        if spm_parameters.get("local-space"):
            mesh_matrix = mathutils.Matrix()
        else:
            mesh_matrix = obj.matrix_world.copy()

        uv_one = True
        uv_two = True
        if (len(mesh.tessface_uv_textures) > 1):
            if (mesh.tessface_uv_textures.active is None):
                uv_one = False
                uv_two = False
        elif (len(mesh.tessface_uv_textures) > 0):
            if (mesh.tessface_uv_textures.active is None):
                uv_one = False
                uv_two = False
            else:
                uv_two = False
        else:
            uv_one = False
            uv_two = False

        for i, f in enumerate(mesh.tessfaces):
            vertex_list = []
            joint_data_list = []

            for j, v in enumerate(f.vertices):
                exported_matrix = axis_conversion * mesh_matrix
                vertex = list(exported_matrix * mesh.vertices[v].co)
                nor_vec = mathutils.Vector(mesh.vertices[v].normal)
                nor_vec.rotate(exported_matrix)
                nor_vec.normalize()
                vertex.extend(nor_vec)
                if uv_one:
                    vertex.append(mesh.tessface_uv_textures[0].data[i].uv[j][0])
                    vertex.append(1 - mesh.tessface_uv_textures[0].data[i].uv[j][1])
                    if mesh.tessface_uv_textures[0].data[i].image != None:
                        vertex.append(os.path.basename(mesh.tessface_uv_textures[0].data[i].image.filepath))
                    else:
                        vertex.append("")
                else:
                    vertex.extend((0.0, 0.0))
                    vertex.append('')
                if uv_two:
                    vertex.append(mesh.tessface_uv_textures[1].data[i].uv[j][0])
                    vertex.append(1 - mesh.tessface_uv_textures[1].data[i].uv[j][1])
                    if mesh.tessface_uv_textures[1].data[i].image != None:
                        vertex.append(os.path.basename(mesh.tessface_uv_textures[1].data[i].image.filepath))
                    else:
                        vertex.append("")
                else:
                    vertex.extend((0.0, 0.0))
                    vertex.append("")
                if (len(mesh.tessface_vertex_colors) > 0):
                    if j == 0:
                        vcolor = mesh.tessface_vertex_colors[0].data[f.index].color1
                    elif j == 1:
                        vcolor = mesh.tessface_vertex_colors[0].data[f.index].color2
                    elif j == 2:
                        vcolor = mesh.tessface_vertex_colors[0].data[f.index].color3
                    elif j == 3:
                        vcolor = mesh.tessface_vertex_colors[0].data[f.index].color4
                    vertex.extend((vcolor.r, vcolor.g, vcolor.b))
                else:
                     vertex.extend((1.0, 1.0, 1.0))

                each_joint_data = []
                for group in mesh.vertices[v].groups:
                    each_joint_data.append((obj.vertex_groups[group.group].name, group.weight))
                vertex_list.append(vertex)
                joint_data_list.append(each_joint_data)

            for t in [2, 1, 0]:
                joint_buf += writeInt(len(joint_data_list[t]))
                for joint_data in joint_data_list[t]:
                    joint_buf += writeString(joint_data[0])
                    joint_buf += writeFloat(joint_data[1])
                buf += write3Float(vertex_list[t][0], vertex_list[t][1], vertex_list[t][2])
                buf += write3Float(vertex_list[t][3], vertex_list[t][4], vertex_list[t][5])
                buf += write4Float(vertex_list[t][6], vertex_list[t][7], vertex_list[t][9], vertex_list[t][10])
                buf += write3Float(vertex_list[t][12], vertex_list[t][13], vertex_list[t][14])
                buf += writeString(vertex_list[t][8])
                buf += writeString(vertex_list[t][11])
                buf += writeString(arm.data.name if arm != None else "NULL")
            if (len(vertex_list) != 3):
                for t in [3, 2, 0]:
                    joint_buf += writeInt(len(joint_data_list[t]))
                    for joint_data in joint_data_list[t]:
                        joint_buf += writeString(joint_data[0])
                        joint_buf += writeFloat(joint_data[1])
                    buf += write3Float(vertex_list[t][0], vertex_list[t][1], vertex_list[t][2])
                    buf += write3Float(vertex_list[t][3], vertex_list[t][4], vertex_list[t][5])
                    buf += write4Float(vertex_list[t][6], vertex_list[t][7], vertex_list[t][9], vertex_list[t][10])
                    buf += write3Float(vertex_list[t][12], vertex_list[t][13], vertex_list[t][14])
                    buf += writeString(vertex_list[t][8])
                    buf += writeString(vertex_list[t][11])
                    buf += writeString(arm.data.name if arm != None else "NULL")

    spm = open(filename + ".mesh_data",'wb')
    spm.write(buf)
    spm.close()

    if arm_count > 0:
        joint_file = open(filename + ".joint_data",'wb')
        joint_file.write(joint_buf)
        joint_file.close()

    script_file = os.path.realpath(__file__)
    cmd_bin = os.path.dirname(script_file)
    cmd_bin = cmd_bin + "/make_spm"
    cmd_text = [cmd_bin] + [filename] + ["do-sp" if spm_parameters.get("do-sp") else "none"] + [str(arm_count)]
    call(cmd_text)

    end = time.time()

    print("Exported in", (end - start))

# ==== CONFIRM OPERATOR ====
class SPM_Confirm_Operator(bpy.types.Operator):
    bl_idname = ("screen.spm_confirm")
    bl_label = ("File Exists, Overwrite?")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        writeSPMFile(SPM_Confirm_Operator.filepath)
        return {'FINISHED'}

# ==== EXPORT OPERATOR ====

class SPM_Export_Operator(bpy.types.Operator):
    bl_idname = ("screen.spm_export")
    bl_label = ("SPM Export")

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    selected = bpy.props.BoolProperty(name="Export selected only", default = False)
    localsp  = bpy.props.BoolProperty(name="Use local coordinates", default = False)
    applymodifiers = bpy.props.BoolProperty(name="Apply modifiers", default = True)
    do_sp = bpy.props.BoolProperty(name="Do mesh splitting (for space partitioning)", default = False)
    overwrite_without_asking = bpy.props.BoolProperty(name="Overwrite without asking", default = False)
    keyframes_only = bpy.props.BoolProperty(name="Export keyframes only for animated mesh", default = True)
    static_mesh_frame = bpy.props.IntProperty(name="Frame for static mesh usage", default = -1)

    def invoke(self, context, event):
        blend_filepath = context.blend_data.filepath
        if not blend_filepath:
            blend_filepath = "Untitled.spm"
        else:
            blend_filepath = os.path.splitext(blend_filepath)[0] + ".spm"
        self.filepath = blend_filepath

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):

        global spm_parameters
        global the_scene
        spm_parameters["export-selected"] = self.selected
        spm_parameters["local-space"    ] = self.localsp
        spm_parameters["apply-modifiers"] = self.applymodifiers
        spm_parameters["keyframes-only"] = self.keyframes_only
        spm_parameters["static-mesh-frame"] = self.static_mesh_frame
        spm_parameters["do-sp"] = self.do_sp
        the_scene = context.scene

        if self.filepath == "":
            return {'FINISHED'}

        if not self.filepath.endswith(".spm"):
            self.filepath += ".spm"

        print("EXPORT", self.filepath)

        obj_list = []
        try:
            # FIXME: silly and ugly hack, the list of objects to export is passed through
            #        a custom scene property
            obj_list = context.scene.obj_list
        except:
            pass

        if len(obj_list) > 0:
            writeSPMFile(self.filepath, obj_list)
        else:
            if os.path.exists(self.filepath) and not self.overwrite_without_asking:
                SPM_Confirm_Operator.filepath = self.filepath
                bpy.ops.screen.spm_confirm('INVOKE_DEFAULT')
                return {'FINISHED'}
            else:
                writeSPMFile(self.filepath)
        return {'FINISHED'}

# Add to a menu
def menu_func_export(self, context):
    global the_scene
    the_scene = context.scene
    self.layout.operator(SPM_Export_Operator.bl_idname, text="SPM (.spm)")

def register():
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.utils.register_module(__name__)

def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register
