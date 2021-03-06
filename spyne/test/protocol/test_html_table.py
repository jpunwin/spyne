#!/usr/bin/env python
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

import logging
logging.basicConfig(level=logging.DEBUG)

import unittest

from pprint import pformat
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from lxml import html

from spyne.application import Application
from spyne.decorator import srpc
from spyne.model.primitive import Integer
from spyne.model.primitive import String
from spyne.model.primitive import AnyUri
from spyne.model.complex import Array
from spyne.model.complex import ComplexModel
from spyne.protocol.http import HttpRpc
from spyne.protocol.html import HtmlTable
from spyne.service import ServiceBase
from spyne.server.wsgi import WsgiApplication
from spyne.util.test import call_wsgi_app_kwargs, call_wsgi_app


class CM(ComplexModel):
    i = Integer
    s = String

class CCM(ComplexModel):
    c = CM
    i = Integer
    s = String


class TestHtmlColumnTable(unittest.TestCase):
    def test_complex_array(self):
        class SomeService(ServiceBase):
            @srpc(CCM, _returns=Array(CCM))
            def some_call(ccm):
                return [ccm] * 5

        app = Application([SomeService], 'tns', in_protocol=HttpRpc(),
                                out_protocol=HtmlTable(field_name_attr='class'))
        server = WsgiApplication(app)

        out_string = call_wsgi_app_kwargs(server,
                ccm_i='456',
                ccm_s='def',
                ccm_c_i='123',
                ccm_c_s='abc',
            )

        from lxml import etree
        elt = etree.fromstring(out_string)
        print(etree.tostring(elt, pretty_print=True))

        elt = html.fromstring(out_string)
        resp = elt.find_class('some_callResponse')
        assert len(resp) == 1

        row, = elt[0] # thead
        cell = row.findall('th[@class="i"]')
        assert len(cell) == 1
        assert cell[0].text == 'i'

        cell = row.findall('th[@class="s"]')
        assert len(cell) == 1
        assert cell[0].text == 's'

        for row in elt[1]: # tbody
            cell = row.xpath('td[@class="i"]')
            assert len(cell) == 1
            assert cell[0].text == '456'

            cell = row.xpath('td[@class="c"]//td[@class="i"]')
            assert len(cell) == 1
            assert cell[0].text == '123'

            cell = row.xpath('td[@class="c"]//td[@class="s"]')
            assert len(cell) == 1
            assert cell[0].text == 'abc'

            cell = row.xpath('td[@class="s"]')
            assert len(cell) == 1
            assert cell[0].text == 'def'

    def test_string_array(self):
        class SomeService(ServiceBase):
            @srpc(String(max_occurs='unbounded'), _returns=Array(String))
            def some_call(s):
                return s

        app = Application([SomeService], 'tns', in_protocol=HttpRpc(), out_protocol=HtmlTable())
        server = WsgiApplication(app)

        out_string = call_wsgi_app(server, body_pairs=(('s', '1'), ('s', '2')))
        assert out_string == '<table class="some_callResponse"><thead><tr><th>some_callResponse</th></tr></thead><tbody><tr><td>1</td></tr><tr><td>2</td></tr></tbody></table>'

    def test_anyuri_string(self):
        _link = "http://arskom.com.tr/"

        class C(ComplexModel):
            c = AnyUri

        class SomeService(ServiceBase):
            @srpc(_returns=Array(C))
            def some_call():
                return [C(c=_link)]

        app = Application([SomeService], 'tns', in_protocol=HttpRpc(),
                 out_protocol=HtmlTable(field_name_attr='class'))
        server = WsgiApplication(app)

        out_string = call_wsgi_app_kwargs(server)

        elt = html.fromstring(out_string)
        print(html.tostring(elt, pretty_print=True))
        assert elt.xpath('//td[@class="c"]')[0][0].tag == 'a'
        assert elt.xpath('//td[@class="c"]')[0][0].attrib['href'] == _link

    def test_anyuri_uri_value(self):
        _link = "http://arskom.com.tr/"
        _text = "Arskom"

        class C(ComplexModel):
            c = AnyUri

        class SomeService(ServiceBase):
            @srpc(_returns=Array(C))
            def some_call():
                return [C(c=AnyUri.Value(_link, text=_text))]

        app = Application([SomeService], 'tns', in_protocol=HttpRpc(),
                 out_protocol=HtmlTable(field_name_attr='class'))
        server = WsgiApplication(app)

        out_string = call_wsgi_app_kwargs(server)

        elt = html.fromstring(out_string)
        print(html.tostring(elt, pretty_print=True))
        assert elt.xpath('//td[@class="c"]')[0][0].tag == 'a'
        assert elt.xpath('//td[@class="c"]')[0][0].text == _text
        assert elt.xpath('//td[@class="c"]')[0][0].attrib['href'] == _link


class TestHtmlRowTable(unittest.TestCase):
    def test_anyuri_string(self):
        _link = "http://arskom.com.tr/"

        class C(ComplexModel):
            c = AnyUri

        class SomeService(ServiceBase):
            @srpc(_returns=C)
            def some_call():
                return C(c=_link)

        app = Application([SomeService], 'tns', in_protocol=HttpRpc(),
                 out_protocol=HtmlTable(field_name_attr='class', fields_as='rows'))
        server = WsgiApplication(app)

        out_string = call_wsgi_app_kwargs(server)

        elt = html.fromstring(out_string)
        print(html.tostring(elt, pretty_print=True))
        assert elt.xpath('//td[@class="c"]')[0][0].tag == 'a'
        assert elt.xpath('//td[@class="c"]')[0][0].attrib['href'] == _link

    def test_anyuri_uri_value(self):
        _link = "http://arskom.com.tr/"
        _text = "Arskom"

        class C(ComplexModel):
            c = AnyUri

        class SomeService(ServiceBase):
            @srpc(_returns=C)
            def some_call():
                return C(c=AnyUri.Value(_link, text=_text))

        app = Application([SomeService], 'tns', in_protocol=HttpRpc(),
                 out_protocol=HtmlTable(field_name_attr='class', fields_as='rows'))
        server = WsgiApplication(app)

        out_string = call_wsgi_app_kwargs(server)

        elt = html.fromstring(out_string)
        print(html.tostring(elt, pretty_print=True))
        assert elt.xpath('//td[@class="c"]')[0][0].tag == 'a'
        assert elt.xpath('//td[@class="c"]')[0][0].text == _text
        assert elt.xpath('//td[@class="c"]')[0][0].attrib['href'] == _link

    def test_complex(self):
        class SomeService(ServiceBase):
            @srpc(CCM, _returns=CCM)
            def some_call(ccm):
                return ccm

        app = Application([SomeService], 'tns', in_protocol=HttpRpc(),
                 out_protocol=HtmlTable(field_name_attr='class', fields_as='rows'))
        server = WsgiApplication(app)

        out_string = call_wsgi_app_kwargs(server,
                         ccm_c_s='abc', ccm_c_i='123', ccm_i='456', ccm_s='def')

        elt = html.fromstring(out_string)
        print(html.tostring(elt, pretty_print=True))

        # Here's what this is supposed to return
        """
        <table class="some_callResponse">
          <tbody>
            <tr>
              <th class="i">i</th>
              <td class="i">456</td>
            </tr>
            <tr class="c">
              <th class="c">c</th>
              <td class="c">
                <table class="c">
                  <tbody>
                    <tr>
                      <th class="i">i</th>
                      <td class="i">123</td>
                    </tr>
                    <tr>
                      <th class="s">s</th>
                      <td class="s">abc</td>
                    </tr>
                  </tbody>
                </table>
              </td>
            </tr>
            <tr>
              <th class="s">s</th>
              <td class="s">def</td>
            </tr>
          </tbody>
        </table>
        """

        resp = elt.find_class('some_callResponse')
        assert len(resp) == 1

        assert elt.xpath('tbody/tr/th[@class="i"]/text()')[0] == 'i'
        assert elt.xpath('tbody/tr/td[@class="i"]/text()')[0] == '456'

        assert elt.xpath('tbody/tr/td[@class="c"]//th[@class="i"]/text()')[0] == 'i'
        assert elt.xpath('tbody/tr/td[@class="c"]//td[@class="i"]/text()')[0] == '123'

        assert elt.xpath('tbody/tr/td[@class="c"]//th[@class="s"]/text()')[0] == 's'
        assert elt.xpath('tbody/tr/td[@class="c"]//td[@class="s"]/text()')[0] == 'abc'

        assert elt.xpath('tbody/tr/th[@class="s"]/text()')[0] == 's'
        assert elt.xpath('tbody/tr/td[@class="s"]/text()')[0] == 'def'

    def test_string_array(self):
        class SomeService(ServiceBase):
            @srpc(String(max_occurs='unbounded'), _returns=Array(String))
            def some_call(s):
                return s

        app = Application([SomeService], 'tns', in_protocol=HttpRpc(), out_protocol=HtmlTable(fields_as='rows'))
        server = WsgiApplication(app)

        out_string = call_wsgi_app(server, body_pairs=(('s', '1'), ('s', '2')) )
        assert out_string == '<table class="some_callResponse"><tbody><tr><th>string</th><td>1</td></tr><tr><th>string</th><td>2</td></tr></tbody></table>'

    def test_string_array_no_header(self):
        class SomeService(ServiceBase):
            @srpc(String(max_occurs='unbounded'), _returns=Array(String))
            def some_call(s):
                return s

        app = Application([SomeService], 'tns', in_protocol=HttpRpc(),
                out_protocol=HtmlTable(fields_as='rows', produce_header=False))
        server = WsgiApplication(app)

        out_string = call_wsgi_app(server, body_pairs=(('s', '1'), ('s', '2')) )
        assert out_string == '<table class="some_callResponse"><tbody><tr><td>1</td></tr><tr><td>2</td></tr></tbody></table>'

if __name__ == '__main__':
    unittest.main()
