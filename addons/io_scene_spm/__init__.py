#!BPY

# Copyright (c) 2017 SPM author(s)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
Name: 'SPM format (.spm)...'
Blender: 270
Group: 'Export-Import'
Tooltip: 'Export/ to space partitioned mesh file format (.spm)'
"""

__version__ = "1.0"
__bpydoc__ = """\
"""

# if "bpy" in locals():
#     import importlib
#     if 'spm_export' in locals():
#         importlib.reload(spm_export)

import bpy
import os
from bpy_extras.io_utils import ImportHelper, ExportHelper

from . import spm_export
from . import spm_import

bl_info = {
    "name": "SPM (Space partitioned mesh) Model ExporterImporter",
    "description": "Exports and imports a blender scene or object to/from the SPM format",
    "version": (1, 0),
    "blender": (2, 7, 0),
    "api": 31236,
    "location": "File > Import-Export",
    "category": "Import-Export"
}

# ==== CONFIRM OPERATOR ====


class SPM_Confirm_Operator(bpy.types.Operator):
    bl_idname = ("screen.spm_confirm")
    bl_label = ("File Exists, Overwrite?")

    # TODO find a better way
    file_path = None
    export_settings = {}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, event)

    def execute(self, context):
        return spm_export.save(self.file_path, context, self.export_settings)


class SPM_Import_Operator(bpy.types.Operator, ImportHelper):
    """ Import SPM operator """

    bl_idname = ("screen.spm_import")
    bl_label = ("SPM Import")
    filename_ext = ".spm"
    filter_glob = bpy.props.StringProperty(default="*.spm", options={'HIDDEN'})
    extra_tex_path = bpy.props.StringProperty(name="Texture path(s)", \
                                              description="Extra directory for textures, seperate by ;;")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "extra_tex_path")

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", ))
        spm_import.load(context, **keywords)
        context.scene.update()
        return {"FINISHED"}


class SPM_Export_Operator(bpy.types.Operator):
    """ Export SPM operator """

    bl_idname = ("screen.spm_export")
    bl_label = ("SPM Export")

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    selected = bpy.props.BoolProperty(name="Export selected only", default=False)
    localsp = bpy.props.BoolProperty(name="Use local coordinates", default=False)
    applymodifiers = bpy.props.BoolProperty(name="Apply modifiers", default=True)
    do_sp = bpy.props.BoolProperty(name="Do mesh splitting (for space partitioning)", default=False)
    overwrite_without_asking = bpy.props.BoolProperty(name="Overwrite without asking", default=False)
    keyframes_only = bpy.props.BoolProperty(name="Export keyframes only for animated mesh", default=True)
    export_normal = bpy.props.BoolProperty(name="Export normal in mesh", default=True)
    export_vcolor = bpy.props.BoolProperty(name="Export vertex color in mesh", default=True)
    export_tangent = bpy.props.BoolProperty(name="Calculate tangent and bitangent sign for mesh", default=True)
    static_mesh_frame = bpy.props.IntProperty(name="Frame for static mesh usage", default=-1)

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

        export_settings = {
            "export-selected": self.selected,
            "local-space": self.localsp,
            "apply-modifiers": self.applymodifiers,
            "keyframes-only": self.keyframes_only,
            "export-normal": self.export_normal,
            "export-vcolor": self.export_vcolor,
            "export-tangent": self.export_tangent,
            "static-mesh-frame": self.static_mesh_frame,
            "do-sp": self.do_sp
        }

        if self.filepath == "":
            return {'FINISHED'}

        if not self.filepath.endswith(".spm"):
            self.filepath += ".spm"

        print("EXPORT", self.filepath)

        if os.path.exists(self.filepath) and not self.overwrite_without_asking:
            SPM_Confirm_Operator.file_path = self.filepath
            SPM_Confirm_Operator.export_settings = export_settings
            bpy.ops.screen.spm_confirm('INVOKE_DEFAULT')
            return {'FINISHED'}

        obj_list = []
        try:
            obj_list = context.scene.obj_list
        except AttributeError:
            pass

        return spm_export.save(self.filepath, context, export_settings, obj_list)


def menu_func_import(self, context):
    """ Add to import menu """
    self.layout.operator(SPM_Import_Operator.bl_idname, text="SPM (.spm)")


def menu_func_export(self, context):
    """ Add to export menu """
    self.layout.operator(SPM_Export_Operator.bl_idname, text="SPM (.spm)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
