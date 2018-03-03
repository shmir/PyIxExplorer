#!/usr/bin/env

import sys
import logging
from optparse import OptionParser
from six.moves import input

from ixexplorer.api.tclproto import TclClient, TclError

rsa_id = 'C:/Program Files (x86)/Ixia/IxOS/8.20-EA/TclScripts/lib/ixTcl1.0/id_rsa'


def main():
    usage = 'usage: %prog [options] <host>'
    parser = OptionParser(usage=usage)
    parser.add_option('-a', action='store_true', dest='autoconnect', help='autoconnect to chassis')
    parser.add_option('-v', action='store_false', dest='verbose', help='be more verbose')
    parser.add_option('-p', dest='port', help='TCP port number', type=int, default=4555)
    parser.add_option('-r', dest='rsa_id', help='RSA ID file', default=rsa_id)

    (options, args) = parser.parse_args()

    logging.basicConfig()
    if options.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    if len(args) < 1:
        print(parser.format_help())
        sys.exit(1)

    host = args[0]

    tcl = TclClient(logging.getLogger('ixexplorer.api'), host, options.port, options.rsa_id)
    tcl.connect()
    if options.autoconnect:
        print(tcl.connect())
        print(tcl.call('chassis add ' + host))
        print(tcl.call('chassis config -id 1'))
        print(tcl.call('chassis set ' + host))

    print("Enter command to send. Quit with 'q'.")
    try:
        io = None
        while True:
            cmd = input('=> ')
            if cmd == 'q':
                break
            if len(cmd) > 0:
                try:
                    res = tcl.call(cmd)
                    print(res.strip())
                    if io is not None:
                        print(io)
                except TclError as e:
                    print('ERROR: %s' % e.result)
    except EOFError:
        print('exitting..')


if __name__ == '__main__':
    main()
