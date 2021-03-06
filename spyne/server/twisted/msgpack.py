# encoding: utf8
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

from __future__ import absolute_import

import logging
logger = logging.getLogger(__name__)

import msgpack

from twisted.internet.defer import Deferred
from twisted.python.log import err
from twisted.internet.protocol import Protocol

from spyne.auxproc import process_contexts
from spyne.error import ValidationError, InternalError
from spyne.model import Fault
from spyne.server.msgpack import MsgPackServerBase


class TwistedMessagePackProtocol(Protocol):
    def __init__(self, app):
        # FIXME: So, how do we prevent the buffer from growing indefinitely?
        self._buffer = msgpack.Unpacker()
        self._transport = MsgPackServerBase(app)

    def dataReceived(self, data):
        self._buffer.feed(data)

        for msg in self._buffer:
            p_ctx = others = None
            try:
                p_ctx, others = self._transport.produce_contexts(msg)
                return self.process_contexts(p_ctx, others)

            except ValidationError as e:
                import traceback
                traceback.print_exc()
                logger.exception(e)
                self.handle_error(p_ctx, others, e)

    def handle_error(self, p_ctx, others, exc):
        self.transport.write(msgpack.packb(str(exc)))
        self.transport.loseConnection()

    def process_contexts(self, p_ctx, others):
        if p_ctx.in_error:
            self.handle_error(p_ctx, others, p_ctx.in_error)
            return

        self._transport.get_in_object(p_ctx)
        if p_ctx.in_error:
            logger.error(p_ctx.in_error)
            self.handle_error(p_ctx, others, p_ctx.in_error)
            return

        self._transport.get_out_object(p_ctx)
        if p_ctx.out_error:
            self.handle_error(p_ctx, others, p_ctx.out_error)
            return

        ret = p_ctx.out_object[0]
        if isinstance(ret, Deferred):
            ret.addCallback(_cb_deferred, self, p_ctx, others)
            ret.addErrback(_eb_deferred)
            return ret

        _cb_deferred(p_ctx.out_object, self, p_ctx, others, nowrap=True)


def _eb_deferred(retval, prot, p_ctx, others):
    p_ctx.out_error = retval.value
    if not issubclass(retval.type, Fault):
        retval.printTraceback()
        p_ctx.out_error = InternalError(retval.value)

    ret = prot.handle_rpc_error(p_ctx, others, p_ctx.out_error)
    prot.transport.write(ret)
    prot.transport.loseConnection()

def _cb_deferred(retval, prot, p_ctx, others, nowrap=False):
    if len(p_ctx.descriptor.out_message._type_info) > 1 or nowrap:
        p_ctx.out_object = retval
    else:
        p_ctx.out_object = [retval]

    try:
        prot._transport.get_out_string(p_ctx)
        p_ctx.out_string = list(p_ctx.out_string)
        print "PC", p_ctx.out_string
        prot.transport.write(''.join(p_ctx.out_string))

    except:
        err(retval)

    finally:
        p_ctx.close()

    process_contexts(prot._transport, others, p_ctx)
