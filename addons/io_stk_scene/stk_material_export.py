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
import bpy.path
import os
from . import config


# ------------------------------------------------------------------------------
# Gets an id property of an object, returning the default if the id property
# is not set. If set_value_if_undefined is set and the property is not
# defined, this function will also set the property to this default value.


def get_id_property(obj, name, default="", set_value_if_undefined=1):
    try:
        prop = obj[name]
        if isinstance(prop, str):
            return obj[name].replace('&', '&amp;')    # this is XML
        else:
            return prop
    except:
        if default is not None and set_value_if_undefined:
            obj[name] = default
    return default


# --------------------------------------------------------------------------
# Write several ways of writing true/false as Y/N


def convert_text_to_yes_no(sText):
    sTemp = sText.strip().upper()
    if sTemp == "0" or sTemp[0] == "N" or sTemp == "FALSE":
        return "N"
    else:
        return "Y"


# Writes the materials files, which includes all texture definitions
# (remember: Blenders "image" objects are STK's "material" objects)
# Please use the STKProperty browser!!!
def write_material_file(sPath):

    # Work around the bug in blender where textures keep disappearing, by forcefully pinning all textures.
    for img in bpy.data.images:
        img.use_fake_user = True

    # Read & Write the materials to the file
    limage = bpy.data.images

    materfound = False
    for i in limage:
        for sAttrib in i.keys():
            materfound = True
            break

    if not materfound:
        print("No Materials defined.")
        return

    lMaterialProperties = {
        'fog': {
            'default': "Y",
            'parent': None,
            'type': 'bool'
        },
        'backface_culling': {
            'default': "Y",
            'parent': None,
            'type': 'bool'
        },
        'below_surface': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'collision_detect': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'collision_particles': {
            'default': "",
            'parent': 'collision_detect',
            'type': 'string'
        },
        'collision_reaction': {
            'default': "none",
            'parent': 'collision_detect',
            'type': 'string'
        },
        'clampu': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'clampv': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'disable_z_write': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'falling_effect': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'gloss_map': {
            'default': "",
            'parent': None,
            'type': 'string'
        },
        'combined_map': {
            'default': "",
            'parent': None,
            'type': 'string'
        },
        'grass_speed': {
            'default': 0.4,
            'parent': ('shader', 'grass'),
            'type': 'number'
        },
        'grass_amplitude': {
            'default': 0.25,
            'parent': ('shader', 'grass'),
            'type': 'number'
        },
        'ignore': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'mask': {
            'default': "",
            'parent': None,
            'type': 'string'
        },
        'mirror_axis': {
            'default': "none",
            'parent': None,
            'type': 'string'
        },
        'normal_map': {
            'default': "",
            'parent': None,
            'type': 'string'
        },
        'reset': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'surface': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'high_adhesion': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'has_gravity': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'slowdown_time': {
            'default': 1.0,
            'parent': 'use_slowdown',
            'type': 'number'
        },
        'max_speed': {
            'default': 1.0,
            'parent': 'use_slowdown',
            'type': 'number'
        },
        'shader': {
            'default': 'solid',
            'parent': None,
            'type': 'string'
        },
        'splatting_texture_1': {
            'default': "",
            'parent': ('shader', 'splatting'),
            'type': 'string'
        },
        'splatting_texture_2': {
            'default': "",
            'parent': ('shader', 'splatting'),
            'type': 'string'
        },
        'splatting_texture_3': {
            'default': "",
            'parent': ('shader', 'splatting'),
            'type': 'string'
        },
        'splatting_texture_4': {
            'default': "",
            'parent': ('shader', 'splatting'),
            'type': 'string'
        },
        'splatting_lightmap': {
            'default': "",
            'parent': ('shader', 'splatting'),
            'type': 'string'
        },
    #'water_shader_speed_1'  : {'default': 6.6667, 'parent': ('graphical_effect','water_shader'), 'type': 'number'},
    #'water_shader_speed_2'  : {'default': 4.0, 'parent': ('graphical_effect','water_shader'), 'type': 'number'},
        'water_splash': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'colorizable': {
            'default': "N",
            'parent': None,
            'type': 'bool'
        },
        'colorization_factor': {
            'default': "",
            'parent': 'colorizable',
            'type': 'number'
        },
        'colorization_mask': {
            'default': "",
            'parent': 'colorizable',
            'type': 'string'
        },
        'hue_settings': {
            'default': "",
            'parent': 'colorizable',
            'type': 'string'
        }
    }

    #start_time = bsys.time()
    print("Writing material file --> \t")

    f = open(sPath + "/materials.xml", mode="w", encoding="utf-8")
    f.write("<?xml version=\"1.0\"?>\n")
    f.write("<!-- Generated with script from SVN rev %s -->\n" % config.get_script_version())
    f.write("<materials>\n")

    blendfile_dir = os.path.dirname(bpy.data.filepath)
    for i in limage:

        # Do not export materials from libraries
        if i.library is not None:
            continue

        # Only export materials from the same directory as the blend file
        abs_texture_path = bpy.path.abspath(i.filepath)
        if not bpy.path.is_subdir(abs_texture_path, blendfile_dir):
            continue

        # iterate through material definitions and collect data
        sImage = ""
        sSFX = ""
        sParticle = ""
        sZipper = ""
        hasSoundeffect = (convert_text_to_yes_no(get_id_property(i, "use_sfx", "no")) == "Y")
        hasParticle = (convert_text_to_yes_no(get_id_property(i, "particle", "no")) == "Y")
        hasZipper = (convert_text_to_yes_no(get_id_property(i, "zipper", "no")) == "Y")

        # Create a copy of the list of defaults so that it can be modified. Then add
        # all properties of the current image
        l = []
        for sAttrib in i.keys():
            if sAttrib not in l:
                l.append((sAttrib, i[sAttrib]))

        for AProperty, ADefault in l:
            # Don't add the (default) values to the property list
            currentValue = get_id_property(i, AProperty, ADefault, set_value_if_undefined=0)

            # Correct for all the ways booleans can be represented (true/false;yes/no;zero/not_zero)
            if AProperty in lMaterialProperties and lMaterialProperties[AProperty]['type'] == 'bool':
                currentValue = convert_text_to_yes_no(currentValue)

            # These items pertain to the soundeffects (starting with sfx_)
            if AProperty.strip().startswith("sfx_"):
                strippedName = AProperty.strip()[len("sfx_"):]

                if strippedName in [
                    'filename', 'rolloff', 'min_speed', 'max_speed', 'min_pitch', 'max_pitch', 'positional', 'volume'
                ]:
                    if isinstance(currentValue, float):
                        sSFX = "%s %s=\"%.2f\"" % (sSFX, strippedName, currentValue)
                    else:
                        sSFX = "%s %s=\"%s\"" % (sSFX, strippedName, currentValue)
            elif AProperty.strip().upper().startswith("PARTICLE_"):
                # These items pertain to the particles (starting with particle_)
                strippedName = AProperty.strip()[len("PARTICLE_"):]
                sParticle = "%s %s=\"%s\"" % (sParticle, strippedName, currentValue)
            elif AProperty.strip().upper().startswith("ZIPPER_"):
                # These items pertain to the zippers (starting with zipper_)
                strippedName = AProperty.strip()[len("ZIPPER_"):]

                sZipper = "%s %s=\"%s\"" % (sZipper, strippedName.replace('_', '-'), currentValue)
            else:
                # These items are standard items
                prop = AProperty.strip()    # .lower()

                if prop in lMaterialProperties.keys():

                    # if this property is conditional on another
                    cond = lMaterialProperties[prop]['parent']

                    conditionPassed = False
                    if cond is None:
                        conditionPassed = True
                    elif type(cond) is tuple:
                        if cond[0] in i and i[cond[0]] == cond[1]:
                            conditionPassed = True
                    elif cond in i and i[cond] == "true":
                        conditionPassed = True

                    if currentValue != lMaterialProperties[prop]['default'] and conditionPassed:
                        if isinstance(currentValue, float):
                            # In blender, proeprties use '_', but STK still expects '-'
                            sImage = "%s %s=\"%.2f\"" % (sImage, AProperty.replace("_", "-"), currentValue)
                        else:
                            # In blender, proeprties use '_', but STK still expects '-'
                            sImage = "%s %s=\"%s\"" % (
                                sImage, AProperty.replace("_", "-"), (currentValue + '').strip()
                            )

        # Now write the main content of the materials.xml file
        if sImage or hasSoundeffect or hasParticle or hasZipper:
            # Get the filename of the image.
            s = i.filepath
            sImage = "  <material name=\"%s\"%s" % (bpy.path.basename(s), sImage)
            if hasSoundeffect:
                sImage = "%s>\n    <sfx%s/" % (sImage, sSFX)
            if hasParticle:
                sImage = "%s>\n    <particles%s/" % (sImage, sParticle)
            if hasZipper:
                sImage = "%s>\n    <zipper%s/" % (sImage, sZipper)
            if not hasSoundeffect and not hasParticle and not hasZipper:
                sImage = "%s/>\n" % (sImage)
            else:
                sImage = "%s>\n  </material>\n" % (sImage)

            f.write(sImage)

    f.write("</materials>\n")

    f.close()
    # print bsys.time()-start_time,"seconds"
    # ----------------------------------------------------------------------





