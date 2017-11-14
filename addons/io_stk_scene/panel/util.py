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
from .constants import *


def get_object(context, contextLevel):
    if contextLevel == CONTEXT_OBJECT:
        return context.object
    if contextLevel == CONTEXT_SCENE:
        return context.scene
    if contextLevel == CONTEXT_MATERIAL:
        if 'selected_image' in context.scene:
            selected_image = context.scene['selected_image']
            if selected_image in bpy.data.images:
                return bpy.data.images[selected_image]

    return None


def get_simple_hash(x):
    import hashlib
    import base64
    m = hashlib.md5()
    m.update(x.encode('ascii'))
    return base64.b64encode(m.digest()).decode('ascii').replace('=', '').replace('/', '_').replace('+',


def generate_operator_name(prefix, fullid, id):
    if len(prefix + fullid + '_' + id) > 60:
        return prefix + get_simple_hash(fullid) + '_' + id
    else:
        return prefix + fullid + '_' + id
