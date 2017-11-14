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

import xml.dom.minidom
from .properties import *
import getpass


def create_properties(object, props):
    """
    Utility function, creates all properties in a given object
    :param object: the object to create properties in
    :param props: a list of properties to create
    :return:
    """
    if not "_RNA_UI" in object:
        object["_RNA_UI"] = {}

    for p in props.keys():

        if isinstance(props[p], StkLabelPseudoProperty):
            continue

        elif isinstance(props[p], StkProperyGroup):
            create_properties(object, props[p].subproperties)

        elif not p in object:

            # create property by setting default value
            v = props[p].default
            object[p] = v

            if isinstance(props[p], StkEnumProperty):
                if v in props[p].values:
                    create_properties(object, props[p].values[v].subproperties)
            elif isinstance(props[p], StkBoolProperty):
                if v == "true":
                    create_properties(object, props[p].subproperties)

        # check the property has the right type
        elif isinstance(props[p], StkFloatProperty):

            if not isinstance(object[p], float):
                try:
                    object[p] = float(object[p])
                except:
                    object[p] = props[p].default

        elif isinstance(props[p], StkIntProperty):

            if not isinstance(object[p], int):
                try:
                    object[p] = int(object[p])
                except:
                    object[p] = props[p].default

        elif isinstance(props[p], StkProperty) and not isinstance(object[p], str):
            try:
                object[p] = str(object[p])
            except:
                object[p] = props[p].default

        rna_ui_dict = {}
        try:
            rna_ui_dict["description"] = props[p].doc
        except:
            pass

        try:
            if props[p].min is not None:
                rna_ui_dict["min"] = props[p].min
                rna_ui_dict["soft_min"] = props[p].min
        except:
            pass

        try:
            if props[p].max is not None:
                rna_ui_dict["max"] = props[p].max
                rna_ui_dict["soft_max"] = props[p].max
        except:
            pass

        object["_RNA_UI"][p] = rna_ui_dict

        if isinstance(props[p], StkEnumProperty):
            if object[p] in props[p].values:
                create_properties(object, props[p].values[object[p]].subproperties)
        elif isinstance(props[p], StkBoolProperty):
            if object[p] == "true":
                create_properties(object, props[p].subproperties)


def parse_properties(node, contextLevel, idprefix):

    props = []

    for e in node.childNodes:
        if e.localName == None:
            continue

        elif e.localName == "StringProp":
            defaultval = e.getAttribute("default")
            if defaultval == "$user":
                defaultval = getpass.getuser()

            if e.hasAttribute("doc"):
                props.append(
                    StkProperty(
                        id=e.getAttribute("id"),
                        fullid=idprefix + '_' + e.getAttribute("id"),
                        name=e.getAttribute("name"),
                        default=defaultval,
                        doc=e.getAttribute("doc")
                    )
                )
            else:
                props.append(
                    StkProperty(
                        id=e.getAttribute("id"),
                        fullid=idprefix + '_' + e.getAttribute("id"),
                        name=e.getAttribute("name"),
                        default=defaultval
                    )
                )

        elif e.localName == "EnumProp":

            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = e.getAttribute("default")

            # if e.hasAttribute("unique_prefix"):
            #    args["unique_prefix"] = e.getAttribute("unique_prefix")

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")

            args["values"] = read_enum_values(e.childNodes, contextLevel, args["fullid"])
            args["contextLevel"] = contextLevel

            props.append(StkEnumProperty(**args))

        elif e.localName == "CombinableEnumProp":

            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = e.getAttribute("default")

            # if e.hasAttribute("unique_prefix"):
            #    args["unique_prefix"] = e.getAttribute("unique_prefix")

            args["values"] = read_enum_values(e.childNodes, contextLevel, args["fullid"])
            args["contextLevel"] = contextLevel

            props.append(StkCombinableEnumProperty(**args))

        elif e.localName == "IntProp":
            if e.hasAttribute("doc"):
                props.append(
                    StkIntProperty(
                        id=e.getAttribute("id"),
                        fullid=idprefix + '_' + e.getAttribute("id"),
                        name=e.getAttribute("name"),
                        default=int(e.getAttribute("default")),
                        doc=e.getAttribute("doc")
                    )
                )
            else:
                props.append(
                    StkIntProperty(
                        id=e.getAttribute("id"),
                        fullid=idprefix + '_' + e.getAttribute("id"),
                        name=e.getAttribute("name"),
                        default=int(e.getAttribute("default"))
                    )
                )

        elif e.localName == "FloatProp":
            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = float(e.getAttribute("default"))

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")
            if e.hasAttribute("min"):
                args["min"] = float(e.getAttribute("min"))
            if e.hasAttribute("max"):
                args["max"] = float(e.getAttribute("max"))

            props.append(StkFloatProperty(**args))

        elif e.localName == "LabelProp":
            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = None

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")

            props.append(StkLabelPseudoProperty(**args))

        elif e.localName == "ColorProp":
            if e.hasAttribute("doc"):
                props.append(
                    StkColorProperty(
                        id=e.getAttribute("id"),
                        fullid=idprefix + '_' + e.getAttribute("id"),
                        name=e.getAttribute("name"),
                        default=e.getAttribute("default"),
                        doc=e.getAttribute("doc"),
                        contextLevel=contextLevel
                    )
                )
            else:
                props.append(
                    StkColorProperty(
                        id=e.getAttribute("id"),
                        fullid=idprefix + '_' + e.getAttribute("id"),
                        name=e.getAttribute("name"),
                        default=e.getAttribute("default"),
                        contextLevel=contextLevel
                    )
                )

        elif e.localName == "PropGroup":

            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["subproperties"] = parse_properties(e, contextLevel, args["fullid"])
            args["contextLevel"] = contextLevel
            p = StkProperyGroup(**args)
            props.append(p)

        elif e.localName == "BoolProp":

            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = e.getAttribute("default")
            args["subproperties"] = parse_properties(e, contextLevel, args["fullid"])
            args["contextLevel"] = contextLevel

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")

            if e.hasAttribute("box"):
                args["box"] = bool(e.getAttribute("box"))

            props.append(StkBoolProperty(**args))

        elif e.localName == "ObjRefProp":
            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = e.getAttribute("default")
            args["contextLevel"] = contextLevel

            global_env = {}
            local_env = {}
            exec("filterFn = " + e.getAttribute("filter"), global_env, local_env)
            args["filter"] = local_env["filterFn"]

            if e.hasAttribute("static_objects"):
                exec("static_objects_fn = " + e.getAttribute("static_objects"), global_env, local_env)
                args["static_objects"] = local_env["static_objects_fn"]

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")

            # if e.hasAttribute("unique_id_suffix"):
            #    args["unique_id_suffix"] = e.getAttribute("unique_id_suffix")

            if e.hasAttribute("obj_identifier"):
                exec("obj_identifier_fn = " + e.getAttribute("obj_identifier"), global_env, local_env)
                args["obj_identifier"] = local_env["obj_identifier_fn"]

            if e.hasAttribute("obj_text"):
                exec("obj_text_fn = " + e.getAttribute("obj_text"), global_env, local_env)
                args["obj_text"] = local_env["obj_text_fn"]

            props.append(StkObjectReferenceProperty(**args))

    return props


def get_properties_from_xml(filename, contextLevel):
    import os
    idprefix = os.path.splitext(os.path.basename(filename))[0]
    node = xml.dom.minidom.parse(filename)
    for curr in node.childNodes:
        if curr.localName == "Properties":
            return [curr.getAttribute("bl-label"), parse_properties(curr, contextLevel, idprefix)]
    raise Exception("No <Properties> node in " + filename)


def read_enum_values(valueNodes, contextLevel, idprefix):
    import collections
    out = collections.OrderedDict()

    for node in valueNodes:
        if node.localName is None:
            continue
        elif node.localName == "EnumChoice":
            args = dict()
            args["id"] = node.getAttribute("id")
            args["fullid"] = idprefix + '_' + node.getAttribute("id")
            args["name"] = node.getAttribute("label")
            args["subproperties"] = parse_properties(node, contextLevel, idprefix + '_' + node.getAttribute("id"))

            if node.hasAttribute("doc"):
                args["doc"] = node.getAttribute("doc")

            out[node.getAttribute("id")] = StkEnumChoice(**args)
        else:
            print("INTERNAL ERROR : Unexpected tag " + str(node.localName) + " in enum '" + str(node.localName) + "'")

    return out
