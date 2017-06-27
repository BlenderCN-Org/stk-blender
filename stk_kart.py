#  SuperTuxKart - a fun racing game with go-kart
#  Copyright (C) 2006-2017 SuperTuxKart-Team
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

__author__ = ["Joerg Henrichs (hiker), Marianne Gagnon (Auria), xapantu"]
__url__ = ["supertuxkart.sourceforge.net"]
__version__ = "$Revision: 16945 $"
__bpydoc__ = """\
"""

bl_info = {
    "name": "SuperTuxKart Kart Exporter",
    "description": "Exports a blender character/kart to SuperTuxKart",
    "author": "Joerg Henrichs, Marianne Gagnon, Xapantu",
    "version": (4, 0),
    "blender": (2, 5, 9),
    "api": 31236,
    "location": "File > Export",
    "warning": '',  # used for warning icon and text in addons panel
    "wiki_url": "https://supertuxkart.net/Community",
    "tracker_url": "https://github.com/supertuxkart/stk-code/issues",
    "category": "Import-Export"}

import re

import bpy
from mathutils import *

operator = None
the_scene = None

log = []

thelist = []


def getlist(self):
    global thelist
    return thelist


def setlist(self, value):
    global thelist
    thelist = value


def log_info(msg):
    print("INFO:", msg)
    log.append(('INFO', msg))


def log_warning(msg):
    print("WARNING:", msg)
    log.append(('WARNING', msg))


def log_error(msg):
    print("ERROR:", msg)
    log.append(('ERROR', msg))


# ------------------------------------------------------------------------------
# Returns a game logic property
def getProperty(obj, name, default=""):
    try:
        return obj[name]
    except:
        return default


# ------------------------------------------------------------------------------
# Returns the version of this script
def getScriptVersion():
    m = re.search('(\d+)', __version__)
    if m:
        return str(m.group(0))
    return "0.1"


# ------------------------------------------------------------------------------
# Save nitro emitter
def saveNitroEmitter(f, lNitroEmitter, path):
    if len(lNitroEmitter) != 2:
        log_warning("Warning - %d nitro emitter specified. Only 2 are allowed" % len(lNitroEmitter))
        return

    f.write('  <nitro-emitter>\n')
    f.write('    <nitro-emitter-a position = "%f %f %f" />\n'
            % (lNitroEmitter[0].location.x, lNitroEmitter[0].location.z, lNitroEmitter[0].location.y))
    f.write('    <nitro-emitter-b position = "%f %f %f" />\n'
            % (lNitroEmitter[1].location.x, lNitroEmitter[1].location.z, lNitroEmitter[1].location.y))
    f.write('  </nitro-emitter>\n')


# ------------------------------------------------------------------------------

def saveHeadlights(f, lHeadlights, path):
    if not lHeadlights:
        return
    if 'b3d_export' not in dir(bpy.ops.screen):
        log_error("Cannot find the B3D exporter, make sure you installed it properly")
        return

    f.write('  <headlights>\n')
    for obj in lHeadlights:
        f.write('    <object position="%f %f %f" model="%s.b3d"/>\n' \
                % (obj.location.x, obj.location.z, obj.location.y, obj.name))

        lOldPos = Vector([obj.location.x, obj.location.y, obj.location.z])
        obj.location = Vector([0, 0, 0])

        global the_scene
        the_scene.obj_list = [obj]

        bpy.ops.screen.b3d_export(localsp=False, mipmap=True, lights=False, vcolors=True,
                                  vnormals=True, cameras=False, filepath=path + "/" + obj.name,
                                  overwrite_without_asking=True)
        the_scene.obj_list = []

        obj.location = lOldPos

    f.write('  </headlights>\n')


# ------------------------------------------------------------------------------
# Save speed weighted
def saveSpeedWeighted(f, lSpeedWeighted, path):
    if not lSpeedWeighted:
        return
    if 'b3d_export' not in dir(bpy.ops.screen):
        log_error("Cannot find the B3D exporter, make sure you installed it properly")
        return

    f.write('  <speed-weighted-objects>\n')
    for obj in lSpeedWeighted:
        strengthFactor = float(getProperty(obj, "speed-weighted-strength-factor", -1.0))
        speedFactor = float(getProperty(obj, "speed-weighted-speed-factor", -1.0))
        textureSpeedX = float(getProperty(obj, "speed-weighted-texture-speed-x", 0.0))
        textureSpeedY = float(getProperty(obj, "speed-weighted-texture-speed-y", 0.0))

        strAttributes = ""
        if strengthFactor >= 0.0:
            strAttributes = strAttributes + ' strength-factor="%f"' % strengthFactor
        if speedFactor >= 0.0:
            strAttributes = strAttributes + ' speed-factor="%f"' % speedFactor
        if textureSpeedX != 0.0 or textureSpeedY != 0.0:
            strAttributes = strAttributes + ' texture-speed-x="%f" texture-speed-y="%f"' % (
            textureSpeedX, textureSpeedY)

        f.write('    <speed-weighted position="%f %f %f" model="%s.b3d" %s/>\n' \
                % (obj.location.x, obj.location.z, obj.location.y, obj.name, strAttributes))

        lOldPos = Vector([obj.location.x, obj.location.y, obj.location.z])
        obj.location = Vector([0, 0, 0])

        global the_scene
        the_scene.obj_list = [obj]

        bpy.ops.screen.b3d_export(localsp=False, mipmap=True, lights=False, vcolors=True,
                                  vnormals=True, cameras=False, filepath=path + "/" + obj.name,
                                  overwrite_without_asking=True)
        the_scene.obj_list = []

        obj.location = lOldPos

    f.write('  </speed-weighted-objects>\n')


# ------------------------------------------------------------------------------
def saveWheels(f, lWheels, path):
    if not lWheels:
        return
    if 'b3d_export' not in dir(bpy.ops.screen):
        log_error("Cannot find the B3D exporter, make sure you installed it properly")
        return

    if len(lWheels) != 4:
        log_warning("Warning - %d wheels specified" % len(lWheels))

    lWheelNames = ("wheel-front-right.b3d", "wheel-front-left.b3d",
                   "wheel-rear-right.b3d", "wheel-rear-left.b3d")
    lSides = ('front-right', 'front-left', 'rear-right', 'rear-left')

    f.write('  <wheels>\n')
    for wheel in lWheels:
        name = wheel.name.upper()
        # If old stylen names are given, use them to determine
        # which wheel is which.
        # if name=="WHEELFRONT.R":
        #    index=0
        # elif name=="WHEELFRONT.L":
        #    index=1
        # elif name=="WHEELREAR.R":
        #    index=2
        # elif name=="WHEELREAR.L":
        #    index=3
        # else:

        # Otherwise the new style 'type=wheel' is used. Use the x and
        #  y coordinates to determine where the wheel belongs to.
        x = wheel.location.x
        y = wheel.location.y
        index = 0
        if y < 0:
            index = index + 2
        if x < 0:
            index = index + 1

        f.write('    <%s position = "%f %f %f"\n'
                % (lSides[index], wheel.location.x, wheel.location.z, wheel.location.y))
        f.write('                 model    = "%s"       />\n' % lWheelNames[index])
        lOldPos = Vector([wheel.location.x, wheel.location.y, wheel.location.z])
        wheel.location = Vector([0, 0, 0])

        global the_scene
        the_scene.obj_list = [wheel]

        bpy.ops.screen.b3d_export(localsp=False, mipmap=True, lights=False, vcolors=True,
                                  vnormals=True, cameras=False, filepath=path + "/" + lWheelNames[index],
                                  overwrite_without_asking=True)
        the_scene.obj_list = []

        wheel.location = lOldPos

    f.write('  </wheels>\n')


# ------------------------------------------------------------------------------
# Saves any defined animations to the kart.xml file.
def saveAnimations(f):
    global the_scene
    first_frame = the_scene.frame_start
    last_frame = the_scene.frame_end

    # search for animation
    lAnims = []
    lMarkersFound = []
    for i in range(first_frame, last_frame + 1):

        # Find markers at this frame
        for curr in the_scene.timeline_markers:
            if curr.frame == i:
                markerName = curr.name.lower()
                if markerName in \
                        ["straight", "right", "left", "start-winning", "start-winning-loop",
                         "end-winning", "start-losing", "start-losing-loop", "end-losing",
                         "start-explosion", "end-explosion", "start-jump", "start-jump-loop", "end-jump",
                         "turning-l", "center", "turning-r", "repeat-losing", "repeat-winning",
                         "start-speed-weighted", "end-speed-weighted", "backpedal-left",
                         "backpedal", "backpedal-right", "selection-start", "selection-end"]:
                    # Remap marker names
                    if markerName == "turning-l":
                        markerName = "left"
                    if markerName == "turning-r":
                        markerName = "right"
                    if markerName == "center":
                        markerName = "straight"
                    if markerName == "repeat-losing":
                        markerName = "start-losing-loop"
                    if markerName == "repeat-winning":
                        markerName = "start-winning-loop"

                    lAnims.append((markerName, i - 1))
                    lMarkersFound.append(markerName)

    if ("straight" not in lMarkersFound) or ("left" not in lMarkersFound) or ("right" not in lMarkersFound):
        log_warning(
            'Could not find markers left/straight/right in frames %i to %i, steering animations may not work'
            % (first_frame, last_frame))

    if ("start-winning" not in lMarkersFound) or ("start-losing" not in lMarkersFound) or (
     "end-winning" not in lMarkersFound) or ("end-losing" not in lMarkersFound):
        log_warning(
            'Could not find markers for win/lose animations in frames %i to %i, win/lose animations may not work'
            % (first_frame, last_frame))

    if lAnims:
        f.write('  <animations %s = "%s"' % (lAnims[0][0], lAnims[0][1]))
        for (marker, frame) in lAnims[1:]:
            f.write('\n              %s = "%s"' % (marker, frame))
        f.write('/>\n')


# ------------------------------------------------------------------------------
# Code for saving kart specific sounds. This is not yet supported, but for
# now I'll leave the code in plase
def saveSounds(f, engine_sfx):
    lSounds = []
    if engine_sfx:
        lSounds.append(("engine", engine_sfx))
    # if kart_sound_horn.val  != "": lSounds.append( ("horn-sound", kart_sound_horn.val ))
    # if kart_sound_crash.val != "": lSounds.append( ("crash-sound",kart_sound_crash.val))
    # if kart_sound_shoot.val != "" :lSounds.append( ("shoot-sound",kart_sound_shoot.val))
    # if kart_sound_win.val   != "" :lSounds.append( ("win-sound",  kart_sound_win.val  ))
    # if kart_sound_explode.val!="" :lSounds.append( ("explode-sound",kart_sound_explode.val))
    # if kart_sound_goo.val   != "" :lSounds.append( ("goo-sound",  kart_sound_goo.val))
    # if kart_sound_pass.val  != "" :lSounds.append( ("pass-sound", kart_sound_pass.val))
    # if kart_sound_zipper.val!= "" :lSounds.append( ("zipper-sound",kart_sound_zipper.val))
    # if kart_sound_name.val  != "" :lSounds.append( ("name-sound", kart_sound_name.val))
    # if kart_sound_attach.val!= "" :lSounds.append( ("attach-sound",kart_sound_attach.val))

    if lSounds:
        f.write('  <sounds %s = "%s"' % (lSounds[0][0], lSounds[0][1]))
        for (name, sound) in lSounds[1:]:
            f.write('\n          %s = "%s"' % (name, sound))
        f.write('/>\n')


# ------------------------------------------------------------------------------
# Exports the actual kart.
def exportKart(path):
    global the_scene
    kart_name_string = the_scene['name']

    if not kart_name_string:
        log_error("No kart name specified")
        return

    color = the_scene['color']
    if color is None:
        log_error("Incorrect kart color")
        return

    split_color = color.split()
    if len(split_color) != 3:
        log_error("Incorrect kart color")
        return

    try:
        split_color[0] = "%.2f" % (int(split_color[0]) / 255.0)
        split_color[1] = "%.2f" % (int(split_color[1]) / 255.0)
        split_color[2] = "%.2f" % (int(split_color[2]) / 255.0)
    except:
        log_error("Incorrect kart color")
        return

    # b3d_export.b3d_parameters["vertex-normals" ] = 1  # Vertex normals.
    # b3d_export.b3d_parameters["vertex-colors"  ] = 1  # Vertex colors
    # b3d_export.b3d_parameters["cameras"        ] = 0  # Cameras
    # b3d_export.b3d_parameters["lights"         ] = 0  # Lights
    # b3d_export.b3d_parameters["mipmap"         ] = 1  # Enable mipmap
    # b3d_export.b3d_parameters["local-space"    ] = 0  # Export in world space

    # Get the kart and all wheels
    # ---------------------------
    lObj = bpy.data.objects
    lWheels = []
    lKart = []
    lNitroEmitter = []
    lSpeedWeighted = []
    lHeadlights = []
    for obj in lObj:
        stktype = getProperty(obj, "type", "").strip().upper()
        name = obj.name.upper()
        if stktype == "WHEEL":
            lWheels.append(obj)
        elif stktype == "NITRO-EMITTER":
            lNitroEmitter.append(obj)
        elif stktype == "SPEED-WEIGHTED":
            lSpeedWeighted.append(obj)
        elif stktype == "IGNORE":
            pass
        elif stktype == "HEADLIGHT":
            lHeadlights.append(obj)
        # For backward compatibility
        # elif name in ["WHEELFRONT.R","WHEELFRONT.L", \
        #              "WHEELREAR.R", "WHEELREAR.L"     ]:
        #    lWheels.append(obj)
        else:
            # Due to limitations with the b3d exporter animated
            # objects must be first in the list of objects to export:
            if obj.parent and obj.parent.type == "Armature":
                lKart.insert(0, obj)
            else:
                lKart.append(obj)

    # Write the xml file
    # ------------------
    kart_shadow = the_scene['shadow']
    if not kart_shadow:
        kart_shadow = kart_name_string.lower() + "_shadow.png"

    kart_icon = the_scene['icon']
    if not kart_icon:
        kart_icon = kart_name_string.lower() + "_icon.png"

    kart_map_icon = the_scene['minimap_icon']
    if not kart_map_icon:
        kart_map_icon = kart_name_string.lower() + "_map_icon.png"

    kart_group = the_scene['group']
    if not kart_group:
        kart_group = "default"

    kart_engine_sfx = the_scene['engine_sfx']
    if not kart_engine_sfx:
        kart_engine_sfx = "small"

    kart_type = 'medium'
    if 'karttype' in the_scene:
        kart_type = the_scene['karttype']

    f = open(path + "/kart.xml", 'w', encoding="utf-8")
    f.write('<?xml version="1.0"?>\n')
    f.write('<!-- Generated with script from SVN rev %s -->\n' \
            % getScriptVersion())

    model_file = kart_name_string.lower() + ".b3d"
    f.write('<kart name              = "%s"\n' % kart_name_string)
    f.write('      version           = "2"\n')
    f.write('      model-file        = "%s"\n' % model_file)
    f.write('      icon-file         = "%s"\n' % kart_icon)
    f.write('      minimap-icon-file = "%s"\n' % kart_map_icon)
    f.write('      shadow-file       = "%s"\n' % kart_shadow)
    f.write('      type              = "%s"\n' % kart_type)

    center_shift = the_scene['center_shift']
    if center_shift and center_shift != 0:
        f.write('      center-shift      = "%.2f"\n' % center_shift)

    f.write('      groups            = "%s"\n' % kart_group)
    f.write('      rgb               = "%s %s %s" >\n' % tuple(split_color))

    saveSounds(f, kart_engine_sfx)
    saveAnimations(f)
    saveWheels(f, lWheels, path)
    saveNitroEmitter(f, lNitroEmitter, path)
    saveSpeedWeighted(f, lSpeedWeighted, path)
    saveHeadlights(f, lHeadlights, path)

    hat_offset = "0.0 1.0 0.0"
    if 'hat_offset' in the_scene and the_scene['hat_offset']:
        hat_offset = the_scene['hat_offset']

    f.write('  <hat offset="' + hat_offset + '"/>\n')

    if 'kartLean' in the_scene and the_scene['kartLean']:
        f.write('  <lean max="' + the_scene['kartLean'] + '"/>\n')

    f.write('</kart>\n')
    f.close()

    the_scene.obj_list = lKart

    if 'b3d_export' not in dir(bpy.ops.screen):
        log_error("Cannot find the B3D exporter, make sure you installed it properly")
        return

    bpy.ops.screen.b3d_export(localsp=False, mipmap=True, lights=False, vcolors=True,
                              vnormals=True, cameras=False, filepath=path + "/" + model_file,
                              overwrite_without_asking=True)
    the_scene.obj_list = []

    # b3d_export.write_b3d_file(Blender.sys.join(path, model_file), lKart)

    # materials file
    # ----------
    if 'stk_material_exporter' not in dir(bpy.ops.screen):
        log_error("Cannot find the material exporter, make sure you installed it properly")
        return

    bpy.ops.screen.stk_material_exporter(filepath=path)

    import datetime
    now = datetime.datetime.now()
    log_info("Export completed on " + now.strftime("%Y-%m-%d %H:%M"))


# ==============================================================================
def savescene_callback(path):
    # Settings for the b3d exporter:
    # b3d_export.b3d_parameters["vertex-normals" ] = 1  # Vertex normals.
    # b3d_export.b3d_parameters["vertex-colors"  ] = 1  # Vertex colors
    # b3d_export.b3d_parameters["cameras"        ] = 0  # Cameras
    # b3d_export.b3d_parameters["lights"         ] = 0  # Lights
    # b3d_export.b3d_parameters["mipmap"         ] = 1  # Enable mipmap
    # b3d_export.b3d_parameters["local-space"    ] = 0  # Export in world space

    global log
    log = []

    exporter = exportKart(path)


# ==== EXPORT OPERATOR ====
class STK_Kart_Export_Operator(bpy.types.Operator):
    bl_idname = ("screen.stk_kart_export")
    bl_label = ("SuperTuxKart Kart Export")
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):

        if bpy.context.mode != 'OBJECT':
            self.report({'ERROR'}, "You must be in object mode")
            log_error("You must be in object mode")
            return {'FINISHED'}

        if 'is_stk_kart' not in context.scene or context.scene['is_stk_kart'] != 'true':
            log_error("Not a STK kart!")
            return {'FINISHED'}

        blend_filepath = context.blend_data.filepath
        if not blend_filepath:
            blend_filepath = "Untitled"
        else:
            import os
            blend_filepath = os.path.splitext(blend_filepath)[0]
        self.filepath = blend_filepath

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):

        if bpy.context.mode != 'OBJECT':
            self.report({'ERROR'}, "You must be in object mode")
            log_error("You must be in object mode")
            return {'FINISHED'}

        if self.filepath == "" or 'is_stk_kart' not in context.scene or context.scene['is_stk_kart'] != 'true':
            return {'FINISHED'}

        global operator
        operator = self

        # FIXME: silly and ugly hack, the list of objects to export is passed through
        #        a custom scene property
        # FIXME: both the kart export script and the track export script do this!! conflicts in sight?
        bpy.types.Scene.obj_list = property(getlist, setlist)

        import os.path
        savescene_callback(os.path.dirname(self.filepath))
        return {'FINISHED'}


class STK_Copy_Log_Operator(bpy.types.Operator):
    bl_idname = ("screen.stk_kart_copy_log")
    bl_label = ("Copy Log")

    def execute(self, context):
        global log
        bpy.data.window_managers[0].clipboard = str(log)
        return {'FINISHED'}


class STK_Clean_Log_Operator(bpy.types.Operator):
    bl_idname = ("screen.stk_kart_clean_log")
    bl_label = ("Clean Log")

    def execute(self, context):
        global log
        log = []
        print("Log cleaned")
        return {'FINISHED'}


# ==== PANEL ====
class STK_Kart_Exporter_Panel(bpy.types.Panel):
    bl_label = "Kart Exporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        global the_scene
        the_scene = context.scene

        layout = self.layout

        # ==== Types group ====
        row = layout.row()

        row.operator("screen.stk_kart_export", "Export", icon='AUTO')

        if bpy.context.mode != 'OBJECT':
            row.enabled = False

        # ==== Output Log ====

        global log

        if log:
            box = layout.box()
            row = box.row()
            row.label("Log")

            for type, msg in log:
                if type == 'INFO':
                    row = box.row()
                    row.label(msg, icon='INFO')
                elif type == 'WARNING':
                    row = box.row()
                    row.label("WARNING: " + msg, icon='ERROR')
                elif type == 'ERROR':
                    row = box.row()
                    row.label("ERROR: " + msg, icon='CANCEL')

            row = box.row()
            row.operator("screen.stk_kart_clean_log", text="Clear Log", icon='X')
            row.operator("screen.stk_kart_copy_log", text="Copy Log", icon='COPYDOWN')


# Add to a menu
def menu_func_export(self, context):
    global the_scene
    the_scene = context.scene
    self.layout.operator(STK_Kart_Export_Operator.bl_idname, text="STK Kart")


def register():
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.utils.register_module(__name__)


def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
