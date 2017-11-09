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

import bpy
import struct
import bmesh

SPM_VERSION = 1


def generate_mesh_buffer(
        spm, vertices_count, indices_count, read_normal, read_vcolor, read_tangent, uv_one, uv_two, is_skinned,
        material_map, material_id
):
    vertices_list = []
    idx_size = \
        4 if vertices_count > 65535 else 2 if vertices_count > 255 else 1
    for vert in range(0, vertices_count):
        vc = None
        u = 0.0
        v = 0.0
        u_2 = 0.0
        v_2 = 0.0
        x, y, z = struct.unpack('<fff', spm.read(12))
        position = (x, z, y)
        if read_normal:
            # Unused, auto re-calculate later
            spm.read(4)
        if read_vcolor:
            # Color identifier
            ci = struct.unpack('<B', spm.read(1))[0]
            if ci == 128:
                # All white
                vc = (1.0, 1.0, 1.0)
            else:
                r, g, b = struct.unpack('<BBB', spm.read(3))
                vc = (r / 255.0, g / 255.0, b / 255.0)
        if uv_one:
            u, v = struct.unpack('<ee', spm.read(4))
            if uv_two:
                u_2, v_2 = struct.unpack('<ee', spm.read(4))
            if read_tangent:
                # Unused
                spm.read(4)
        if is_skinned:
            # Unused
            spm.read(16)
        vertices_list.append((position, vc, (u, v, u_2, v_2)))

    if idx_size == 4:
        indices_list = struct.unpack("%dI" % (indices_count,), spm.read(indices_count * idx_size))
    elif idx_size == 2:
        indices_list = struct.unpack("%dH" % (indices_count,), spm.read(indices_count * idx_size))
    else:
        indices_list = struct.unpack("%dB" % (indices_count,), spm.read(indices_count * idx_size))
    idx = 0

    mesh = bpy.data.meshes.new(str(material_id))
    obj = bpy.data.objects.new(str(material_id), mesh)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    while idx < len(indices_list):
        v1 = bm.verts.new(vertices_list[indices_list[idx + 2]][0])
        v2 = bm.verts.new(vertices_list[indices_list[idx + 1]][0])
        v3 = bm.verts.new(vertices_list[indices_list[idx]][0])
        bm.faces.new((v1, v2, v3))
        idx = idx + 3

    bmesh.ops.remove_doubles(bm, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    bpy.context.scene.objects.link(obj)


def load(context, filepath, extra_tex_path):
    spm = open(filepath, 'rb')

    sp_header = spm.read(2)
    if sp_header != b'SP':
        print('%s is not a valid spm file' % filepath)
        spm.close()
        return

    byte = struct.unpack('<B', spm.read(1))[0]
    version = byte >> 3
    if version != SPM_VERSION:
        print('%d unsupported version' % version)
        spm.close()
        return

    byte &= ~0x08
    header = None
    if byte == 0:
        header = "SPMS"
    elif byte == 1:
        header = "SPMA"
    else:
        header = "SPMN"

    byte = struct.unpack('<B', spm.read(1))[0]
    read_normal = byte & 0x01
    read_vcolor = byte >> 1 & 0x01
    read_tangent = byte >> 2 & 0x01
    is_skinned = header == "SPMA"

    # Skip useless bounding box
    spm.read(24)
    material_count = struct.unpack('<H', spm.read(2))[0]
    material_map = []
    for material in range(0, material_count):
        tex_name_1 = None
        tex_name_2 = None
        tex_size = struct.unpack('<B', spm.read(1))[0]
        if tex_size > 0:
            tex_name_1 = spm.read(tex_size).decode('ascii')
        tex_size = struct.unpack('<B', spm.read(1))[0]
        if tex_size > 0:
            tex_name_2 = spm.read(tex_size).decode('ascii')
        material_map.append((tex_name_1, tex_name_2))

    # Space partitioned mesh sector count, should be 1
    sector_count = struct.unpack('<H', spm.read(2))[0]

    for sector in range(0, sector_count):
        material_count = struct.unpack('<H', spm.read(2))[0]
        for material in range(0, material_count):
            vertices_count = struct.unpack('<I', spm.read(4))[0]
            indices_count = struct.unpack('<i', spm.read(4))[0]
            material_id = struct.unpack('<H', spm.read(2))[0]
            assert material_id < material_count
            generate_mesh_buffer(
                spm, vertices_count, indices_count, read_normal, read_vcolor, read_tangent,
                material_map[material_id][0] is not None, material_map[material_id][1] is not None, is_skinned,
                material_map, material_id
            )

        if header == "SPMS":
            # Reserved, never used
            spm.read(24)
