#!BPY

# Copyright (c) 2017 STK blender addon author(s)
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
Name: 'STK Scene Exporter for Material/Kart/Track...'
Blender: 259
Group: 'Export'
Tooltip: 'Export a SuperTuxKart track scene'
"""
__author__ = ["Joerg Henrichs (hiker), Marianne Gagnon (Auria)"]
__url__ = ["supertuxkart.sourceforge.net"]
__version__ = "$Revision: 17088 $"
__bpydoc__ = """\
"""

import bpy
import os
from bpy_extras.io_utils import ImportHelper, ExportHelper
from . import stk_material_export

bl_info = {
    "name": "STK Scene Exporter for Material/Kart/Track",
    "description": "Exporter scenes for Material/Kart/Track",
    "author": "Joerg Henrichs, Marianne Gagnon",
    "version": (1, 0),
    "blender": (2, 5, 9),
    "api": 31236,
    "location": "File > Export",
    "warning": '',    # used for warning icon and text in addons panel
    "wiki_url": "http://supertuxkart.sourceforge.net/Get_involved",
    "tracker_url": "https://sourceforge.net/apps/trac/supertuxkart/",
    "category": "Import-Export"
}


class STK_Material_Export_Operator(bpy.types.Operator):
    bl_idname = ("screen.stk_material_exporter")
    bl_label = ("Export Materials")
    filepath = bpy.props.StringProperty()

    def execute(self, context):
        stk_material_export.write_material_file(self.filepath)
        return {'FINISHED'}


def menu_func_add_banana(self, context):
    self.layout.operator_menu_enum("scene.stk_add_object", property="value", text="STK", icon='AUTO')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_add.append(menu_func_add_banana)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_add.remove(menu_func_add_banana)
