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
from .util import *
from .stk_property import StkProperty


# ------------------------------------------------------------------------------
#! A text field where you can type a reference to another object (or a property
#! of another object) with an optional dropdown button to see current choices
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! contextLevel     object, scene, material level?
#! default          default value for this property
#! filter           a lambda taking arguments "self" and "object", and that returns
#!                  parameter 'object' is to be displayed in the dropdown of this property
#! doc              documentation to show in the tooltip
#! static_objects   items to append to the menu unconditionally (a list of tuples of
#!                  form 'id', 'visible name')
#! obj_identifier   a lambda taking arguments "self" and "object", and that returns
#!                  the id (value) of an object that should be put in this property when
#!                  the object is selected
#! obj_text         a lambda taking arguments "self" and "object", and that returns
#!                  the user-visible string to apear in the dropdown for an object
class StkObjectReferenceProperty(StkProperty):

    def __init__(
        self,
        id,
        fullid,
        name,
        contextLevel,
        default,
        filter,
        doc="Select an object",
        static_objects=[],
        obj_identifier=lambda self, obj: obj.name,
        obj_text=lambda self, obj: (obj.name + ((" (" + obj["name"] + ")") if "name" in obj else ""))
    ):
        super(StkObjectReferenceProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.doc = doc

        if filter is None:
            raise Exception("Filter may not be None")

        select_op_name = generate_operator_name("screen.stk_select_object_", fullid, id)

        class SelectObjectOperator(bpy.types.Operator):
            bl_idname = select_op_name
            bl_label = "Select Object Operator"
            __doc__ = doc

            m_id = id
            m_context_level = contextLevel

            # name of the object to select
            name = bpy.props.StringProperty()

            def execute(self, context):
                object = get_object(context, self.m_context_level)
                object[self.m_id] = self.name
                return {'FINISHED'}

        bpy.utils.register_class(SelectObjectOperator)

        op_name = generate_operator_name("screen.stk_object_menu_", fullid, id)

        class ObjectPickerMenu(bpy.types.Menu):
            m_filter = filter
            m_obj_identifier = obj_identifier
            m_obj_text = obj_text
            m_static_objects = static_objects
            m_fullid = fullid
            bl_idname = op_name
            bl_label = ("SuperTuxKart Object Picker Menu (" + id + ")")
            m_property_id = id

            def draw(self, context):
                objects = context.scene.objects

                seen_objs = {}

                layout = self.layout
                for object in objects:
                    if self.m_filter(object):
                        text = self.m_obj_text(object)
                        object_id = self.m_obj_identifier(object)

                        if object_id is not None and object_id not in seen_objs:
                            layout.operator(select_op_name, text=text).name = object_id
                            seen_objs[object_id] = True

                for curr in self.m_static_objects:
                    layout.operator("scene.stk_select_object_" + self.m_property_id, text=curr[1]).name = curr[0]

        bpy.utils.register_class(ObjectPickerMenu)
