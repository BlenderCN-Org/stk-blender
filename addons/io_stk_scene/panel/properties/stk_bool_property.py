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
from .stk_property import StkProperty
from ..util import *
from .util import *
from collections import OrderedDict


# ------------------------------------------------------------------------------
#! A boolean property (appears as a checkbox)
#!
#! id                   the id of the blender id-property
#! name                 user-visible name
#! contextLevel         object, scene, material level?
#! default              default value for this property
#! @param subproperties A list of StkProperty's. Contains the properties
#                       that are to be shown when this checkbox is checked
#! box                  if True, the properties from 'subproperties' are
#!                      displayed in a box
#! doc                  documentation shown to the user in a tooltip
class StkBoolProperty(StkProperty):

    # (self, id, name, values, default):
    box = True

    #! A floating-point property
    def __init__(
        self,
        id,
        name,
        contextLevel,
        default="false",
        subproperties=[],
        box=True,
        fullid="",
        doc="(No documentation defined for this element)"
    ):
        super(StkBoolProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)

        self.box = box
        self.contextLevel = contextLevel

        self.subproperties = OrderedDict([])
        for curr in subproperties:
            self.subproperties[curr.id] = curr

        self.doc = doc
        super_self = self

        # Create operator for this bool
        class STK_ToggleBoolValue(bpy.types.Operator):

            bl_idname = generate_operator_name("screen.stk_tglbool_", fullid, id)
            bl_label = ("SuperTuxKart toggle " + id)
            __doc__ = doc

            m_context_level = contextLevel
            m_property_id = id
            m_super_self = super_self

            def execute(self, context):

                # Set the property

                object = get_object(context, self.m_context_level)
                if object is None:
                    return

                curr_val = False
                if self.m_property_id in object:
                    curr_val = (object[self.m_property_id] == "true")

                new_val = not curr_val

                if curr_val:
                    object[self.m_property_id] = "false"
                else:
                    object[self.m_property_id] = "true"

                # If sub-properties are needed, create them
                if object[self.m_property_id] == "true":
                    create_properties(object, self.m_super_self.subproperties)

                return {'FINISHED'}

        bpy.utils.register_class(STK_ToggleBoolValue)
