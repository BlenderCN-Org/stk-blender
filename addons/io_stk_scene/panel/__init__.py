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
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty
from collections import OrderedDict
import os.path
from .util import *
from .properties import *
from .constants import *
from .properties import *


def raise_error(message):
    print(message)
    raise Exception(message)


current_path = os.path.dirname(os.path.realpath(__file__))
addon_path = os.path.dirname(current_path)
data_path = os.path.join(addon_path, "data")

# Load the panel XML properties
if os.path.exists(data_path):
    print("(STK) Loading XML files from ", data_path)
    panel_params_path = os.path.join(data_path, "stk_panel_parameters.xml")
    object_params_path = os.path.join(data_path, "stk_object_parameters.xml")
    kart_params_path = os.path.join(data_path, "stk_kart_object_parameters.xml")
    material_params_path = os.path.join(data_path, "stk_material_parameters.xml")

    if os.path.exists(panel_params_path):
        print("(STK) Loading scene properties from ", panel_params_path)
        SCENE_PROPS = get_properties_from_xml(panel_params_path, contextLevel=CONTEXT_SCENE)
    else:
        raise_error("(STK) failed to load panel params XML")

    if os.path.exists(object_params_path):
        print("(STK) Loading object properties from ", object_params_path)
        STK_PER_OBJECT_TRACK_PROPERTIES = get_properties_from_xml(object_params_path, contextLevel=CONTEXT_OBJECT)
    else:
        raise_error("(STK) failed to load object params XML")

    if os.path.exists(kart_params_path):
        print("(STK) Loading kart properties from ", kart_params_path)
        STK_PER_OBJECT_KART_PROPERTIES = get_properties_from_xml(kart_params_path, contextLevel=CONTEXT_OBJECT)
    else:
        raise_error("(STK) failed to load kart params XML")

    if os.path.exists(material_params_path):
        print("(STK) Loading material properties from ", material_params_path)
        STK_MATERIAL_PROPERTIES = get_properties_from_xml(material_params_path, contextLevel=CONTEXT_MATERIAL)
    else:
        raise_error("(STK) failed to load material params XML")

else:
    raise_error("(STK) Make sure the data folder is installed, cannot locate it!!")


# ==== PANEL BASE ====
class PanelBase:

    def recursivelyAddProperties(self, properties, layout, obj, contextLevel):

        for id in properties.keys():
            curr = properties[id]

            row = layout.row()

            if isinstance(curr, StkProperyGroup):

                state = "true"
                icon = 'TRIA_DOWN'
                if id in bpy.data.scenes[0]:
                    state = bpy.data.scenes[0][id]
                    if state == "true":
                        icon = 'TRIA_DOWN'
                    else:
                        icon = 'TRIA_RIGHT'

                row.operator(
                    generate_operator_name("screen.stk_tglbool_", curr.fullid, curr.id),
                    text=curr.name,
                    icon=icon,
                    emboss=False
                )
                row.label(" ")    # force the operator to not maximize
                if state == "true":
                    if len(curr.subproperties) > 0:
                        box = layout.box()
                        self.recursivelyAddProperties(curr.subproperties, box, obj, contextLevel)

            elif isinstance(curr, StkBoolProperty):

                state = "false"
                icon = 'CHECKBOX_DEHLT'
                split = row.split(0.8)
                split.label(text=curr.name)
                if id in obj:
                    state = obj[id]
                    if state == "true":
                        icon = 'CHECKBOX_HLT'
                split.operator(
                    generate_operator_name("screen.stk_tglbool_", curr.fullid, curr.id),
                    text="                ",
                    icon=icon,
                    emboss=False
                )

                if state == "true":
                    if len(curr.subproperties) > 0:
                        if curr.box:
                            box = layout.box()
                            self.recursivelyAddProperties(curr.subproperties, box, obj, contextLevel)
                        else:
                            self.recursivelyAddProperties(curr.subproperties, layout, obj, contextLevel)

            elif isinstance(curr, StkColorProperty):
                row.label(text=curr.name)
                if curr.id in obj:
                    row.prop(obj, '["' + curr.id + '"]', text="")
                    row.operator(
                        generate_operator_name("screen.apply_color_", curr.fullid, curr.id), text="", icon='COLOR'
                    )
                else:
                    row.operator('screen.stk_missing_props_' + str(contextLevel))

            elif isinstance(curr, StkCombinableEnumProperty):

                row.label(text=curr.name)

                if curr.id in obj:
                    curr_val = obj[curr.id]

                    for value_id in curr.values:
                        icon = 'CHECKBOX_DEHLT'
                        if value_id in curr_val:
                            icon = 'CHECKBOX_HLT'
                        row.operator(
                            generate_operator_name("screen.stk_set_", curr.fullid, curr.id + "_" + value_id),
                            text=curr.values[value_id].name,
                            icon=icon
                        )
                else:
                    row.operator('screen.stk_missing_props_' + str(contextLevel))

            elif isinstance(curr, StkLabelPseudoProperty):
                row.label(text=curr.name)

            elif isinstance(curr, StkEnumProperty):

                row.label(text=curr.name)

                if id in obj:
                    curr_value = obj[id]
                else:
                    curr_value = ""

                label = curr_value
                if curr_value in curr.values:
                    label = curr.values[curr_value].name

                row.menu(curr.menu_operator_name, text=label)
                # row.operator_menu_enum(curr.getOperatorName(), property="value", text=label)

                if curr_value in curr.values and len(curr.values[curr_value].subproperties) > 0:
                    box = layout.box()
                    self.recursivelyAddProperties(curr.values[curr_value].subproperties, box, obj, contextLevel)

            elif isinstance(curr, StkObjectReferenceProperty):

                row.label(text=curr.name)

                if curr.id in obj:
                    row.prop(obj, '["' + curr.id + '"]', text="")
                    row.menu(
                        generate_operator_name("screen.stk_object_menu_", curr.fullid, curr.id),
                        text="",
                        icon='TRIA_DOWN'
                    )
                else:
                    row.operator('screen.stk_missing_props_' + str(contextLevel))

            else:
                row.label(text=curr.name)

                # String or int or float property (Blender chooses the correct widget from the type of the ID-property)
                if curr.id in obj:
                    if "min" in dir(curr) and "max" in dir(curr) and curr.min is not None and curr.max is not None:
                        row.prop(obj, '["' + curr.id + '"]', text="", slider=True)
                    else:
                        row.prop(obj, '["' + curr.id + '"]', text="")
                else:
                    row.operator('screen.stk_missing_props_' + str(contextLevel))


class STK_TypeUnset(bpy.types.Operator):
    bl_idname = ("screen.stk_unset_type")
    bl_label = ("STK Object :: unset type")

    def execute(self, context):
        obj = context.object
        obj["type"] = ""
        return {'FINISHED'}


class STK_MissingProps_Object(bpy.types.Operator):
    bl_idname = ("screen.stk_missing_props_" + str(CONTEXT_OBJECT))
    bl_label = ("Create missing properties")

    def execute(self, context):

        is_track = ("is_stk_track" in context.scene and context.scene["is_stk_track"] == "true")
        is_node = ("is_stk_node" in context.scene and context.scene["is_stk_node"] == "true")
        is_kart = ("is_stk_kart" in context.scene and context.scene["is_stk_kart"] == "true")

        obj = context.object

        if is_kart:
            properties = OrderedDict([])
            for curr in STK_PER_OBJECT_KART_PROPERTIES[1]:
                properties[curr.id] = curr
            create_properties(obj, properties)

        elif is_track or is_node:
            properties = OrderedDict([])
            for curr in STK_PER_OBJECT_TRACK_PROPERTIES[1]:
                properties[curr.id] = curr
            print('creating', properties, 'on', obj.name)
            create_properties(obj, properties)

        return {'FINISHED'}


class STK_MissingProps_Scene(bpy.types.Operator):
    bl_idname = ("screen.stk_missing_props_" + str(CONTEXT_SCENE))
    bl_label = ("Create missing properties")

    def execute(self, context):
        scene = context.scene
        properties = OrderedDict([])
        for curr in SCENE_PROPS[1]:
            properties[curr.id] = curr

        create_properties(scene, properties)
        return {'FINISHED'}


class STK_MissingProps_Material(bpy.types.Operator):
    bl_idname = ("screen.stk_missing_props_" + str(CONTEXT_MATERIAL))
    bl_label = ("Create missing properties")

    def execute(self, context):
        material = get_object(context, CONTEXT_MATERIAL)
        properties = OrderedDict([])
        for curr in STK_MATERIAL_PROPERTIES[1]:
            properties[curr.id] = curr

        create_properties(material, properties)
        return {'FINISHED'}


class STK_SelectImage(bpy.types.Operator):
    bl_idname = ("scene.stk_select_image")
    bl_label = ("STK Object :: select image")

    name = bpy.props.StringProperty()

    def execute(self, context):
        global selected_image
        context.scene['selected_image'] = self.name

        if "STKPreviewTexture" not in bpy.data.textures:
            bpy.ops.scene.stk_create_material_preview()

        if "STKPreviewTexture" in bpy.data.textures:
            if self.name in bpy.data.images:
                bpy.data.textures["STKPreviewTexture"].image = bpy.data.images[self.name]
            else:
                bpy.data.textures["STKPreviewTexture"].image = None
        else:
            print("STK Panel : can't create preview texture!")

        if self.name in bpy.data.images:

            properties = OrderedDict([])
            for curr in STK_MATERIAL_PROPERTIES[1]:
                properties[curr.id] = curr

            create_properties(bpy.data.images[self.name], properties)

        return {'FINISHED'}


class ImagePickerMenu(bpy.types.Menu):
    bl_idname = "scene.stk_image_menu"
    bl_label = "SuperTuxKart Image Menu"

    def draw(self, context):
        import bpy.path

        objects = context.scene.objects

        layout = self.layout
        row = layout.row()
        col = row.column()

        blend_path = os.path.abspath(bpy.path.abspath("//"))
        is_lib_node = ('is_stk_node' in context.scene and context.scene['is_stk_node'] == 'true')

        i = 0
        for curr in bpy.data.images:

            if curr.library is not None:
                continue
            if not is_lib_node and \
                    not os.path.abspath(bpy.path.abspath(curr.filepath)).startswith(blend_path):
                continue

            if i % 20 == 0:
                col = row.column()
            i += 1
            col.operator("scene.stk_select_image", text=curr.name).name = curr.name


# ==== OBJECT PANEL ====
class SuperTuxKartObjectPanel(bpy.types.Panel, PanelBase):
    bl_label = STK_PER_OBJECT_TRACK_PROPERTIES[0]
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):

        layout = self.layout

        is_track = ("is_stk_track" in context.scene and context.scene["is_stk_track"] == "true")
        is_node = ("is_stk_node" in context.scene and context.scene["is_stk_node"] == "true")
        is_kart = ("is_stk_kart" in context.scene and context.scene["is_stk_kart"] == "true")

        if not is_track and not is_kart and not is_node:
            layout.label("(Not a SuperTuxKart scene)")
            return

        obj = context.object

        if obj.proxy is not None:
            layout.label("Library nodes cannot be configured here")
            return

        if obj is not None:
            if is_track or is_node:
                properties = OrderedDict([])
                for curr in STK_PER_OBJECT_TRACK_PROPERTIES[1]:
                    properties[curr.id] = curr
                self.recursivelyAddProperties(properties, layout, obj, CONTEXT_OBJECT)

            if is_kart:
                properties = OrderedDict([])
                for curr in STK_PER_OBJECT_KART_PROPERTIES[1]:
                    properties[curr.id] = curr
                self.recursivelyAddProperties(properties, layout, obj, CONTEXT_OBJECT)


class SuperTuxKartImagePanel(bpy.types.Panel, PanelBase):
    bl_label = STK_MATERIAL_PROPERTIES[0]
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    m_current_image = ''

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        try:
            if "STKPreviewTexture" in bpy.data.textures:
                layout.template_preview(bpy.data.textures["STKPreviewTexture"])
            else:
                layout.label("Sorry, no image preview available")
        except:
            layout.label("Sorry, no image preview available")

        label = "Select an image"
        if 'selected_image' in context.scene:
            label = context.scene['selected_image']

        self.m_op_name = "scene.stk_image_menu"
        # row.label(label)
        row.menu(self.m_op_name, text=label)

        obj = get_object(context, CONTEXT_MATERIAL)
        if obj is not None:

            properties = OrderedDict([])
            for curr in STK_MATERIAL_PROPERTIES[1]:
                properties[curr.id] = curr

            self.recursivelyAddProperties(properties, layout, obj, CONTEXT_MATERIAL)


# Extension to the 'add' menu
class STK_AddObject(bpy.types.Operator):
    bl_idname = ("scene.stk_add_object")
    bl_label = ("STK Object :: add object")

    name = bpy.props.StringProperty()

    value = bpy.props.EnumProperty(
        attr="values",
        name="values",
        default='banana',
        items=[
            ('banana', 'Banana',
             'Banana'), ('item', 'Item (Gift Box)',
                         'Item (Gift Box)'), ('light', 'Light', 'Light'), ('nitro_big', 'Nitro (Big)', 'Nitro (big)'),
            ('nitro_small', 'Nitro (Small)',
             'Nitro (Small)'), ('particle_emitter', 'Particle Emitter',
                                'Particle Emitter'), ('sfx_emitter', 'Sound Emitter', 'Sound Emitter'),
            ('start', 'Start position (for battle mode)', 'Start position (for battle mode)')
        ]
    )

    def execute(self, context):
        if self.value == 'light':
            bpy.ops.object.add(type='LAMP', location=bpy.data.scenes[0].cursor_location)

            for curr in bpy.data.objects:
                if curr.type == 'LAMP' and curr.select:
                    # FIXME: create associated subproperties if any
                    curr['type'] = self.value
                    curr.data.use_sphere = True
                    break
        else:
            bpy.ops.object.add(type='EMPTY', location=bpy.data.scenes[0].cursor_location)

            for curr in bpy.data.objects:
                if curr.type == 'EMPTY' and curr.select:
                    # FIXME: create associated subproperties if any
                    curr['type'] = self.value

                    if self.value == 'item':
                        curr.empty_draw_type = 'CUBE'
                    elif self.value == 'nitro_big' or self.value == 'nitro_small':
                        curr.empty_draw_type = 'CONE'
                    elif self.value == 'sfx_emitter':
                        curr.empty_draw_type = 'SPHERE'

                    for prop in STK_PER_OBJECT_TRACK_PROPERTIES[1]:
                        if prop.name == "Type":
                            create_properties(curr, prop.values[self.value].subproperties)
                            break

                    break

        return {'FINISHED'}


# ==== SCENE PANEL ====
class SuperTuxKartScenePanel(bpy.types.Panel, PanelBase):
    bl_label = SCENE_PROPS[0]
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        obj = context.scene

        if obj is not None:

            properties = OrderedDict([])
            for curr in SCENE_PROPS[1]:
                properties[curr.id] = curr

            self.recursivelyAddProperties(properties, layout, obj, CONTEXT_SCENE)


# ==== IMAGE PANEL ====
class STK_CreateImagePreview(bpy.types.Operator):
    bl_idname = ("scene.stk_create_material_preview")
    bl_label = ("STK :: create material preview")

    name = bpy.props.StringProperty()

    def execute(self, context):

        try:
            bpy.ops.texture.new()
            bpy.data.textures[-1].name = "STKPreviewTexture"
            bpy.data.textures["STKPreviewTexture"].type = 'IMAGE'
            bpy.data.textures["STKPreviewTexture"].use_preview_alpha = True
        except:
            print("Exception caught in createPreviewTexture")
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)

        return {'FINISHED'}


# ======== PREFERENCES ========
class StkPanelAddonPreferences(AddonPreferences):
    bl_idname = 'stk_track'

    stk_assets_path = StringProperty(
        name="Supertuxkart assets (data) folder",
    # subtype='DIR_PATH',
    )

    stk_delete_old_files_on_export = BoolProperty(
        name="Delete all old files when exporting a track in a folder (*.spm)",
    # subtype='DIR_PATH',
    )

    def draw(self, context):
        layout = self.layout
        layout.label(
            text=
            "The data folder contains folders named 'karts', 'tracks', 'textures', etc. Please enter an absolute path."
        )
        layout.prop(self, "stk_assets_path")

        layout.prop(self, "stk_delete_old_files_on_export")


# class STK_AddLightmap(bpy.types.Operator):
#    def execute(self, context):
#        if len(context.object.data.uv_textures) == 0:
#            bpy.ops.mesh.uv_texture_add()
#            context.object.data.uv_textures[-1].name = 'UV'
#        if len(context.object.data.uv_textures) < 2:
#            bpy.ops.mesh.uv_texture_add()
#            context.object.data.uv_textures[-1].name = 'Lightmap'
#
# bpy.utils.register_class(STK_AddLightmap)

# class stkpanel_set_user_preferences(Operator):
#    bl_idname = "object.stkpanel_set_user_preferences"
#    bl_label = "Addon Preferences Example"
#    bl_options = {'REGISTER', 'UNDO'}
#
#    def execute(self, context):
#        user_preferences = context.user_preferences
#        addon_prefs = user_preferences.addons['stk_track'].preferences
#
#        info = ("Path: %s, Number: %d, Boolean %r" %
#                (addon_prefs.filepath, addon_prefs.number, addon_prefs.boolean))
#
#        self.report({'INFO'}, info)
#        print(info)
#
#        return {'FINISHED'}
