# -*- encoding: utf-8 -*-
#
# File name: pdu.py
#
# Written By:
#   Chen Weiwei (Dave.Chen.ww@gmail.com)
#   twinsant@gmail.com
#

import re

import pdu_modem


_debug = True

def main():
    import conf
    import sys
    import logging

    if _debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.debug('Debug messages ready.')
    if len(sys.argv) < 2:
        print 'Usage: pdu message <mobile>'
        sys.exit(1)
    msg = sys.argv[1]
    if len(sys.argv) > 2:
        mobile = pdu_modem.conv_fmt(sys.argv[2])
    else:
        mobile = pdu_modem.conv_fmt(conf.DEBUG_MOBILE)

    modem = None
    try:
        modem = pdu_modem.E61(conf.DEBUG_PORT, conf.DEBUG_BAUD,
                conf.DEBUG_MIN_TIMEOUT, conf.DEBUG_MAX_TIMEOUT)
        modem.send(mobile, msg.decode(conf.DEBUG_ENCODING))
    finally:
        if modem:
            modem.close()

def bench():
    import conf
    import sys
    import logging

    level = logging.INFO
    logging.basicConfig(level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    mobile = pdu_modem.conv_fmt(conf.DEBUG_MOBILE)

    modem = None
    try:
        modem = pdu_modem.E61(conf.DEBUG_PORT, conf.DEBUG_BAUD,
                conf.DEBUG_MIN_TIMEOUT, conf.DEBUG_MAX_TIMEOUT)
        modem.benchmark(10)
    finally:
        if modem:
            modem.close()

if __name__ == '__main__':
    main()
