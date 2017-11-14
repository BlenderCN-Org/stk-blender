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

import bpy
from ..util import *
from .stk_property import StkProperty


# ------------------------------------------------------------------------------
#! A color property
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! contextLevel     object, scene, material level?
#! default          default value for this property
#! doc              documentation shown to the user in a tooltip
class StkColorProperty(StkProperty):

    #! A floating-point property
    def __init__(
        self, id, name, contextLevel, default="255 255 255", fullid="", doc="(No documentation defined for this item)"
    ):
        super(StkColorProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)

        #! Color picker operator (TODO: this operator is mostly for backwards compatibility with our
        #                               blend files that come from 2.4; blender 2.5 has a color property
        #                               type we could use)
        class Apply_Color_Operator(bpy.types.Operator):
            bl_idname = generate_operator_name("screen.apply_color_", fullid, id)
            bl_label = ("Apply Color")
            __doc__ = doc

            property_id = id

            m_context_level = contextLevel

            temp_color = bpy.props.FloatVectorProperty(
                name="temp_color",
                description="Temp Color.",
                subtype='COLOR',
                min=0.0,
                max=1.0,
                soft_min=0.0,
                soft_max=1.0,
                default=(1.0, 1.0, 1.0)
            )

            def invoke(self, context, event):

                currcol = [1.0, 1.0, 1.0]
                try:

                    object = get_object(context, self.m_context_level)
                    if object is None:
                        return

                    currcol = list(map(eval, object[self.property_id].split()))
                    currcol[0] = currcol[0] / 255.0
                    currcol[1] = currcol[1] / 255.0
                    currcol[2] = currcol[2] / 255.0
                except:
                    pass

                if currcol is not None and len(currcol) > 2:
                    self.temp_color = currcol
                context.window_manager.invoke_props_dialog(self)
                return {'RUNNING_MODAL'}

            def draw(self, context):

                layout = self.layout

                # ==== Types group ====
                box = layout.box()
                row = box.row()
                try:
                    row.template_color_picker(self, "temp_color", value_slider=True, cubic=False)
                except Exception as ex:
                    import sys
                    print("Except :(", type(ex), ex, "{", ex.args, "}")
                    pass

                row = layout.row()
                row.prop(self, "temp_color", text="Selected Color")

            def execute(self, context):

                object = get_object(context, self.m_context_level)
                if object is None:
                    return

                object[self.property_id
                       ] = "%i %i %i" % (self.temp_color[0] * 255, self.temp_color[1] * 255, self.temp_color[2] * 255)
                return {'FINISHED'}

        bpy.utils.register_class(Apply_Color_Operator)
