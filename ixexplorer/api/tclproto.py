# Copyright (c) 2015  Kontron Europe GmbH
#
# This module is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this module; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

#
# Protocol parser for IXIA's underlying TclServer
#

import socket
import paramiko
import time
from trafficgenerator.tgn_utils import TgnError


class TclError(Exception):

    def __init__(self, result):
        self.result = result

    def __repr__(self):
        return '%s(result="%s")' % (self.__class__.__name__, self.result)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.result)


class TclClient:

    def __init__(self, logger, host, port=4555, rsa_id=None):
        self.logger = logger
        self.host = host
        self.port = port
        self.rsa_id = rsa_id
        self.fd = None
        self.buffersize = 10240

        import logging
        from os import path
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
        if file_handler:
            logger_file_name = path.splitext(logger.handlers[0].baseFilename)[0]
            tcl_logger_file_name = logger_file_name + '-' + self.__class__.__name__ + '.tcl'
            self.tcl_script = logging.getLogger('tcl' + self.__class__.__name__)
            self.tcl_script.addHandler(logging.FileHandler(tcl_logger_file_name, 'w'))
            self.tcl_script.setLevel(logger.getEffectiveLevel())

    def socket_call(self, string, *args):
        if self.fd is None:
            raise RuntimeError('TclClient is not connected')

        string += '\r\n'
        command = string % args
        self.logger.debug('sending %s', command.rstrip())
        self.tcl_script.debug(command.rstrip())
        self.fd.send(command.encode('utf-8'))

        # reply format is
        #  [<io output>\r]<result><tcl return code>\r\n
        # where tcl_return code is exactly one byte
        reply = str(self.fd.recv(self.buffersize).decode('utf-8'))
        self.logger.debug('received %s', reply.rstrip())
        # print 'data=(%s) (%s)' % (data, data.encode('hex'))
        assert reply[-2:] == '\r\n'

        tcl_result = int(reply[-3])

        data = reply[:-3].rsplit('\r', 1)
        if len(data) == 2:
            io_output, result = data
        else:
            result = data[0]
            io_output = None

        if tcl_result == 1:
            assert not io_output
            raise TclError(result)

        self.logger.debug('result=%s io_output=%s', result, io_output)
        return result, io_output

    def ssh_call(self, string, *args):
        command = 'puts [{}]\n\r'.format(string % args)
        self.logger.debug('sending %s', command.rstrip())
        self.stdin.write(command)
        self.stdin.flush()
        buf_len = len(self.stdout.channel.in_buffer)
        while not buf_len:
            time.sleep(0.25)
            buf_len = len(self.stdout.channel.in_buffer)
        ret_value = str(self.stdout.read(buf_len).decode("utf-8").rstrip())
        self.logger.debug('received %s', ret_value)
        return ret_value

    def call(self, string, *args):
        if self.windows_server:
            result, io_output = self.socket_call(string, *args)
            if io_output and 'Error:' in io_output:
                raise TgnError(io_output)
            return result
        else:
            return self.ssh_call(string, *args)

    def _tcl_hal_version(self):
        rsp = self.call('version cget -ixTclHALVersion')
        return rsp[0].split('.')

    def connect(self):
        self.logger.debug('Opening connection to %s:%d', self.host, self.port)

        if self.port == 8022:
            self.windows_server = False
            key = paramiko.RSAKey.from_private_key_file(self.rsa_id)
            self.fd = paramiko.SSHClient()
            self.fd.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.fd.connect(hostname=self.host, port=self.port, username='ixtcl', pkey=key)
            self.stdin, self.stdout, _ = self.fd.exec_command('')
            self.call('source /opt/ixia/ixos/current/IxiaWish.tcl')
        else:
            self.windows_server = True
            fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            fd.connect((self.host, self.port))
            self.fd = fd

        rc = self.call('package req IxTclHal')
        self.call('enableEvents true')
        print 'rc = ' + rc

    def close(self):
        self.logger.debug('Closing connection')
        self.fd.close()
        self.fd = None

    def hal_version(self):
        """Returns a tuple (major,minor) of the TCL HAL version."""
        return tuple(self._tcl_hal_version()[0:2])
