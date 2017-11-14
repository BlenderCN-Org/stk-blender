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
from collections import OrderedDict


# ------------------------------------------------------------------------------
#! One entry in a StkEnumProperty
class StkEnumChoice:

    #! @param name          User-visible name for this property
    #! @param subproperties A list of StkProperty's. Contains the properties
    #                       that are to be shown when this enum item is selected
    def __init__(self, name, subproperties, id, fullid, doc="(No documentation was defined for this item)"):
        self.name = name
        self.id = id
        self.fullid = fullid

        self.subproperties = OrderedDict([])
        for curr in subproperties:
            self.subproperties[curr.id] = curr

        self.doc = doc


# ------------------------------------------------------------------------------
#! An enum property
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! values           the choices offered by this enum, as a list of 'StkEnumChoice' objects
#! contextLevel     object, scene, material level?
#! default          default value for this property
class StkEnumProperty(StkProperty):

    def getOperatorName(self):
        return self.operator_name

    #! @param name   User-visible name for this property
    #! @param values A dictionnary of type { 'value' : StkEnumChoice(...) }
    #! @note         The first value will be used by default
    def __init__(self, id, name, values, contextLevel, default, fullid, doc="(No documentation for this item)"):
        super(StkEnumProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.values = values
        self.fullid = fullid
        self.operator_name = generate_operator_name("screen.stk_set_", fullid, id)
        self.menu_operator_name = generate_operator_name("screen.stkmenu_set_", fullid, id)
        self.doc = doc
        default_value = default

        values_for_blender_unsorted = []
        for curr_val in values.keys():
            if len(curr_val) > 0:
                curr_obj = values[curr_val]
                values_for_blender_unsorted.append((curr_val, curr_obj.name, curr_obj.name + " : " + curr_obj.doc))

        #values_for_blender = sorted(values_for_blender_unsorted, key=lambda k: k[1])
        values_for_blender = values_for_blender_unsorted

        class STK_CustomMenu(bpy.types.Menu):
            bl_idname = generate_operator_name("screen.stkmenu_set_", fullid, id)
            bl_label = ("SuperTuxKart set " + id)
            __doc__ = doc

            def draw(self, context):
                import bpy.path

                layout = self.layout
                row = layout.row()
                col = row.column()

                for curr in values_for_blender_unsorted:
                    if curr[0].startswith('__category__'):
                        col.label(text=curr[1])
                    elif curr[0].startswith('__column_break__'):
                        col = row.column()
                    else:
                        col.operator(
                            generate_operator_name("screen.stk_set_", fullid, id), text=curr[1]
                        ).value = curr[0]

        bpy.utils.register_class(STK_CustomMenu)

        # Create operator for this combo
        class STK_SetComboValue(bpy.types.Operator):

            value = bpy.props.EnumProperty(
                attr="values", name="values", default=default_value + "", items=values_for_blender
            )

            bl_idname = generate_operator_name("screen.stk_set_", fullid, id)
            bl_label = ("SuperTuxKart set " + id)
            __doc__ = doc

            m_property_id = id
            m_items_val = values_for_blender
            m_values = values
            m_context_type = contextLevel

            def execute(self, context):

                # Set the property
                object = get_object(context, self.m_context_type)
                if object is None:

                    return

                object[self.m_property_id] = self.value

                # If sub-properties are needed, create them
                if self.value in self.m_values:
                    create_properties(object, self.m_values[self.value].subproperties)

                return {'FINISHED'}

        bpy.utils.register_class(STK_SetComboValue)


# ------------------------------------------------------------------------------
#! A combinable enum property (each value can be checked or unchecked, and
#! several values can be selected at once. gives a text property containing
#! the IDs of the selected values, separated by spaces)
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! values           the choices offered by this enum, as a list of 'StkEnumChoice' objects
#! contextLevel     object, scene, material level?
#! default          default value for this property
class StkCombinableEnumProperty(StkProperty):

    #! @param name   User-visible name for this property
    #! @param values A dictionnary of type { 'value' : StkEnumChoice(...) }
    #! @note         The first value will be used by default
    def __init__(self, id, name, values, contextLevel, default, fullid):
        super(StkCombinableEnumProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.values = values

        default_value = default

        values_for_blender = []
        for curr_val in values.keys():
            curr_obj = values[curr_val]
            values_for_blender.append(curr_val)

        for curr in values_for_blender:
            # Create operator for this combo
            class STK_SetEnumComboValue(bpy.types.Operator):

                bl_idname = generate_operator_name("screen.stk_set_", fullid, id + "_" + curr)
                bl_label = ("SuperTuxKart set " + id + " = " + curr)

                if values[curr].doc is not None:
                    __doc__ = values[curr].doc + ""

                m_property_id = id
                m_items_val = values_for_blender
                m_values = values
                m_context_type = contextLevel
                m_curr = curr

                def execute(self, context):

                    # Set the property
                    object = get_object(context, self.m_context_type)
                    if object is None:
                        return

                    if self.m_property_id not in object:
                        object[self.m_property_id] = ""

                    if self.m_curr in object[self.m_property_id]:
                        # Remove selected value
                        l = object[self.m_property_id].split()
                        l.remove(self.m_curr)
                        object[self.m_property_id] = " ".join(l)
                    else:
                        # Add selected value
                        object[self.m_property_id] = object[self.m_property_id] + \
                            " " + self.m_curr

                    return {'FINISHED'}

            bpy.utils.register_class(STK_SetEnumComboValue)
