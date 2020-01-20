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
import select
import sys

from trafficgenerator.tgn_utils import TgnError, new_log_file


class Error(Exception):
    """Base class for all future-related exceptions."""
    pass


class TclError(Exception):

    def __init__(self, result):
        self.result = result

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.result)


class TclClient:

    def __init__(self, logger, host, port=4555, rsa_id=None):
        self.logger = logger
        self.host = host
        self.port = port
        self.rsa_id = rsa_id
        self.fd = None
        self.buffersize = 2 ** 12

        self.tcl_script = new_log_file(self.logger, self.__class__.__name__)

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
        reply = ''
        for _ in range(16 * 100):
            reply += str(self.fd.recv(self.buffersize).decode('utf-8'))
            if reply.endswith('\r\n'):
                break
            time.sleep(0.01)
        if not reply:
            raise Exception('no response after 16 seconds')
        self.logger.debug('received %s', reply.rstrip())
        assert reply[-2:] == '\r\n'

        tcl_result = int(reply[-3])
        data = reply[:-3].rsplit('\r', 1)
        if len(data) == 2:
            if data[-1].isdigit():
                io_output, result = data
            else:
                # Handle 'streamRegion generateWarningList' where we actually care about the output so we put it into
                # the result...
                result = reply[:-3]
                io_output = None
        else:
            result = data[0]
            io_output = None

        if tcl_result == 1:
            assert not io_output
            raise TclError(result)

        self.logger.debug('result=%s io_output=%s', result, io_output)
        return result, io_output

    def ssh_call_shell(self, string, *args):
        result, io_output = '',None
        string += '\r\n'
        command = string % args
        self.logger.debug('sending %s', command.rstrip())
        self.tcl_script.debug(command.rstrip())
        reply = ''
        resuls_space = '\r\r\n'
        if 'ixCheckTransmitDone' in command:
            orig = self.ssh_shell.command_timeout
            self.ssh_shell.command_timeout = 300
            reply = self.ssh_shell.send_receive(command.encode('utf-8'))
            self.ssh_shell.command_timeout = orig
        else:
            reply = self.ssh_shell.send_receive(command.encode('utf-8'))
        reply = reply.rstrip(resuls_space)[2:]
        self.logger.debug('received %s', reply.rstrip())
        if len(reply):
            data = reply.rsplit(resuls_space, 1)
            if len(data) ==  2:
                io_output, result = data
            else:
                result = data[0]
                io_output = None
        else:
            self.logger.debug('probably command without result')
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
        else:
            #return self.ssh_call(string, *args)
            result, io_output = self.ssh_call_shell(string, *args)
        if io_output and 'Error:' in io_output:
            raise TgnError(io_output)
        return result


    def connect(self):
        self.logger.debug('Opening connection to %s:%d', self.host, self.port)

        if self.port == 8022:
            self.windows_server = False
            key = paramiko.RSAKey.from_private_key_file(self.rsa_id)
            self.fd = paramiko.SSHClient()
            self.fd.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.fd.connect(hostname=self.host, port=self.port, username='ixtcl', pkey=key)
            self.ssh_shell = sshWraper(self.fd)
            #self.stdin, self.stdout, _ = self.fd.exec_command('')
            self.call('source /opt/ixia/ixos/current/IxiaWish.tcl')
        else:
            self.windows_server = True
            fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            fd.settimeout(60.0)
            fd.connect((self.host, self.port))
            self.fd = fd

        self.call('package req IxTclHal')
        self.call('enableEvents true')

    def close(self):
        self.logger.debug('Closing connection')
        self.fd.close()
        self.fd = None


class sshWraper(object):

    default_eofOutput = '\r\n% % '
    _command_timeout = 10
    shell = None
    default_buffer_size = 4096
    PY3K = sys.version_info >= (3, 0)

    def __init__(self,channel):
        self._shell = channel.invoke_shell()

    def write(self, cmd):
        if self._shell:
            return self._shell.send(cmd)

    def read_all(self):
        ret_str = ""
        if self._shell:
            while self._shell.recv_ready():
                res = self._shell.recv(sshWraper.default_buffer_size)
                ret_str += str(res)
        return ret_str

    @property
    def command_timeout(self):
        return sshWraper._command_timeout

    @command_timeout.setter
    def command_timeout(self, timeout):
        sshWraper._command_timeout = timeout

    def read_until(self, eoOut= None):
        timeout = self.command_timeout
        prompt = eoOut.encode() if eoOut else sshWraper.default_eofOutput.encode()
        line = bytearray()
        if self._shell:
            lenterm = len(prompt)
            time_start = time.time()
            reply_tuple = ([self._shell], [], [])
            args_tuple = reply_tuple
            if timeout is not None:
                args_tuple = args_tuple + (timeout,)
            while select.select(*args_tuple) == reply_tuple:
                c = self._shell.recv(1)
                if c:
                    line += c
                    if len(line) >= lenterm and line[-lenterm:] == prompt:
                        break
                if timeout is not None:
                    elapsed = time.time() - time_start
                    if elapsed >= timeout:
                        break
                    args_tuple = reply_tuple + (timeout - elapsed,)

        res = bytes(line).decode() if sshWraper.PY3K else bytes(line)
        return res

    def send_receive(self,cmd):
        reply = ''
        self.read_all()
        self.write(cmd)
        fullreply = self.read_until()
        if fullreply.count('Invalid') > 0:
            raise TclError(fullreply)
        if fullreply:
            reply = fullreply.rstrip(sshWraper.default_eofOutput)
            reply = reply[len(cmd):]
        return reply



