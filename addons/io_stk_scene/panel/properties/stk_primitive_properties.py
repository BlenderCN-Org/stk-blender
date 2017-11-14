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

from .stk_property import StkProperty


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
