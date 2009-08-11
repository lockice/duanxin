# -*- encoding: utf-8 -*-
#
# File name: pdu.py
#
# Written By:
#   Chen Weiwei (Dave.Chen.ww@gmail.com)
#   twinsant@gmail.com
#

import re

import SMS_PDU_Modem


def is_mobile(mobile):
    ret = False
    if len(mobile) == 11:
        # 130-139 150-153 155-159 186 188 189
        if re.match(r'1(3[0-9]|5[0-35-9]|8[689])\d{8}', mobile):
            ret = True
    return ret

def conv_fmt(mobile):
    if is_mobile(mobile):
        return '+86%s' % mobile
    elif not mobile.startswith('+86') or not is_mobile(mobile[3:]):
        raise 'Not valid mobile number: %s' % mobile
    else:
        return mobile

if __name__ == '__main__':
    import conf
    import sys
    if len(sys.argv) < 2:
        print 'Usage: pdu message <mobile>'
        sys.exit(1)
    msg = sys.argv[1]
    if len(sys.argv) > 2:
        mobile = conv_fmt(sys.argv[2])
    else:
        mobile = conv_fmt(conf.DEBUG_MOBILE)
    modem = SMS_PDU_Modem.SMS_PDU_Modem('/dev/ttyACM0', 115200)
    modem.send(mobile, msg.decode('utf-8'))


