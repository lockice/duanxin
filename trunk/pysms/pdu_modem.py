# -*- encoding: utf-8 -*-
#
# File name: pdu_modem.py
#
# Written by: Chen Weiwei (Dave.Chen.ww@gmail.com)
# Refactoring by: twinsant@gmail.com
#
# Code reference: Python sms package, http://pypi.python.org/pypi/sms

import re
import time

import serial

import pdu_util


class ModemError(RuntimeError):
    pass


class PDUModem(object):
    """Provides access to a gsm modem
    """

    def __init__(self, dev_id, baud):
        self.conn = serial.Serial(dev_id, baud, timeout=1, rtscts=1)
        # make sure modem is OK
        self._command('AT')
        # set pdu mode
        self._command('AT+CMGF=0')
        self.pdu = pdu_util.PduUtil()
        # find smsc
        smsc_re = re.compile('\+CSCA: "(?P<smsc>.+)"')
        smsc_cmd_out = self._command('AT+CSCA?')
        for s in smsc_cmd_out:
            m = smsc_re.match(s)
            if m is not None:
                self.smsc = m.group('smsc')
                break

    def send(self, number, message):
        """Send a SMS message"""
        commands = self.pdu.meta_info_to_pdu(message, '+86'+str(number),
                                             self.smsc, 16)
        for length, msg in commands:
            self._command('AT+CMGS=%d\r%s\x1A' % (length, msg), flush=False)
            wait = True
            while wait:
                time.sleep(1)
                results = self.conn.readlines()
                for s in results:
                    if 'OK' in s:
                        wait = False
                        break

    def messages(self, list=4):
        """Return received messages, list type:
        0(received unread), 1(received read), 2(stored unsent), 3(stored sent),
        4(all, default)
        """
        msgs = []
        msg_item_re = re.compile('\+CMGL:')
        # pdu mode, list all msgs
        msg_cmd_out = self._command('AT+CMGL=%d' % list)
        for i in range(len(msg_cmd_out)):
            m = msg_item_re.match(msg_cmd_out[i])
            if m is not None:
                msgs.append(self.pdu.get_pdu_meta_info(
                    msg_cmd_out[i+1].strip('\r\n')))
                i += 1
            i += 1
        return msgs

    def _command(self, at_command, flush=True):
        self.conn.write(at_command)
        if flush:
            self.conn.write('\r')
        results = self.conn.readlines()
        for line in results:
            if 'ERROR' in line:
                raise ModemError(results)
        return results

    def __del__(self):
        try:
            self.conn.close()
        except AttributeError:
            pass


if __name__ == '__main__':
    modem = pdu_modem(4, 115200) # port='COM5', baud=115200
    user_choice = raw_input('Send(s)? Read(r)? Quit(q)? ')
    while (user_choice == 's' or user_choice == 'r'):
        if (user_choice == 's'):
            mobile = raw_input(
                '\nInput a mobile phone number (eg. 13812345678): ')
            msg = raw_input('\nInput message: ')
            msg_unicode = msg.decode('cp936')
            print '\nSending to number: %s, with msg:\n\t%s\n' % (
                mobile, msg_unicode)
            modem.send(mobile, msg_unicode)
            print '\nOK!\n'
        elif (user_choice == 'r'):
            list_type = raw_input('\nInput list type (0-4): ')
            try:
                list = int(list_type)
                if list < 0 or list > 4:
                    list = 4
            except Exception:
                list = 4
            print '\nListing msgs...\n'
            msgs = modem.messages(list)
            for i in range(len(msgs)):
                print 'Message %d:\n' % (i+1)
                print msgs[i]
                print '-'*20
            print '\nOK!\n'
        user_choice = raw_input('\nSend(s)? Read(r)? Quit(q)? ')
    else:
        print '\n\nQuiting...'
        modem.conn.close()
        del(modem)
