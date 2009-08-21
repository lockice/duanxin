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


if __name__ == '__main__':
    import conf
    import sys
    import logging

    logging.basicConfig(level=logging.DEBUG,
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

    try:
        modem = pdu_modem.PDUModem(conf.DEBUG_PORT, conf.DEBUG_BAUD, conf.DEBUG_MIN_TIMEOUT)
        modem.send(mobile, msg.decode(conf.DEBUG_ENCODING))
    finally:
        modem.close()
