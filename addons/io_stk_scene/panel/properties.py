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
from .util import *
from .properties_utils import *
from collections import OrderedDict


class StkProperty:
    """
    The base class for all properties.
    If you use this property directly (and not a subclass), you get a simple text box
    """

    def __init__(self, id, name, default, fullid, doc="(No documentation was defined for this item)"):
        self.name = name
        self.id = id
        self.fullid = fullid
        self.default = default
        self.doc = doc

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
                        col.operator(generate_operator_name("screen.stk_set_", fullid, id), text=curr[1]).value = curr[0]

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


# ------------------------------------------------------------------------------
#! A pseudo-property that only displays some text
class StkLabelPseudoProperty(StkProperty):

    def __init__(
        self, id, name, default=0.0, doc="(No documentation defined for this element)", fullid="", min=None, max=None
    ):
        super(StkLabelPseudoProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.default
        self.doc = doc


# ------------------------------------------------------------------------------
#! A floating-point property
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! default          default value for this property
#! doc              documentation shown to the user in a tooltip
#! min              minimum accepted value
#! max              maximum accepted value
class StkFloatProperty(StkProperty):

    #! @param name   User-visible name for this property
    def __init__(
        self, id, name, default=0.0, doc="(No documentation defined for this element)", fullid="", min=None, max=None
    ):
        super(StkFloatProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.default
        self.doc = doc
        self.min = min
        self.max = max


# ------------------------------------------------------------------------------
#! An integer property
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! default          default value for this property
#! doc              documentation shown to the user in a tooltip
#! min              minimum accepted value
#! max              maximum accepted value
class StkIntProperty(StkProperty):

    #! @param name   User-visible name for this property
    def __init__(
        self, id, name, default=0, doc="(No documentation defined for this element)", fullid="", min=None, max=None
    ):
        super(StkIntProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.doc = doc
        self.min = min
        self.max = max


# ------------------------------------------------------------------------------


class StkProperyGroup(StkProperty):

    #! A floating-point property
    def __init__(
        self,
        id,
        name,
        contextLevel,
        default="false",
        subproperties=[],
        fullid="",
        doc="(No documentation defined for this element)"
    ):
        super(StkProperyGroup, self).__init__(id=id, name=name, default=default, fullid=fullid)

        self.contextLevel = contextLevel

        self.subproperties = OrderedDict([])
        for curr in subproperties:
            self.subproperties[curr.id] = curr

        self.doc = doc
        super_self = self

        # Create operator for this bool
        class STK_TogglePropGroupValue(bpy.types.Operator):

            bl_idname = generate_operator_name("screen.stk_tglbool_", fullid, id)
            bl_label = ("SuperTuxKart toggle " + id)
            __doc__ = doc

            m_context_level = contextLevel
            m_property_id = id
            m_super_self = super_self

            def execute(self, context):

                # Set the property

                object = bpy.data.scenes[0]
                if object is None:
                    return

                curr_val = True
                if self.m_property_id in object:
                    curr_val = (object[self.m_property_id] == "true")

                new_val = not curr_val

                if curr_val:
                    object[self.m_property_id] = "false"
                else:
                    object[self.m_property_id] = "true"

                propobject = get_object(context, self.m_context_level)
                if propobject is None:
                    return

                # If sub-properties are needed, create them
                if object[self.m_property_id] == "true":
                    create_properties(propobject, self.m_super_self.subproperties)

                return {'FINISHED'}

        bpy.utils.register_class(STK_TogglePropGroupValue)


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
