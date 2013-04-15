
#
# spyne - Copyright (C) Spyne contributors.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#


from spyne.model.complex import Array
from spyne.protocol.dictdoc import HierDictDocument


def get_dict_as_object(d, cls):
    if issubclass(cls, Array):
        d = list(d.values())[0] # FIXME: Hack!

    return HierDictDocument._doc_to_object(cls, d)


def get_object_as_dict(o, cls, wrapper_name=None, ignore_wrappers=False,
                                                                complex_as=list):
    return HierDictDocument(ignore_wrappers=ignore_wrappers,
                    complex_as=complex_as)._object_to_doc(cls, o, wrapper_name)