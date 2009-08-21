# -*- encoding: utf-8 -*-
#
# File name: pdu_modem.py
#
# Written by: Chen Weiwei (Dave.Chen.ww@gmail.com)
# Refactoring by: twinsant@gmail.com
#
# Code reference: Python sms package, http://pypi.python.org/pypi/sms

import logging
import re
import time

# Check serial.serialutil and serial.serialposix for more information
import serial

import pdu_util


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


class ModemError(RuntimeError):
    pass

class TimeoutError(Exception):
    def __init__(self, read_interval, total_timeout):
        self.read_interval = read_interval
        self.total_timeout = total_timeout

    def __str__(self):
        return 'Read interval %.2fs(total %.2fs), reconnect your device and retry.' % (
                    self.read_interval, self.total_timeout)

class PDUModem(object):
    """Provides access to a gsm modem
    """

    def __init__(self, dev_id, baud, min_timeout=0.1, max_timeout=6):
        self.min_timeout = min_timeout
        self.max_timeout = max_timeout
        self.conn = serial.Serial(dev_id, baud, rtscts=1)
        # make sure modem is OK
        self._command('AT')
        # set pdu mode
        self._command('AT+CMGF=0')
        self.pdu = pdu_util.PDUUtil()
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
        commands = self.pdu.meta_info_to_pdu(message, conv_fmt(number),
                                             self.smsc, 16)
        for length, msg in commands:
            # send msg command: AT+CMGS=<length><CR><pdu><Ctrl-Z>
            results = self._command('AT+CMGS=%d\r%s\x1A' % (length, msg))

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
        logging.debug('Command: %s' % repr(at_command))
        self.conn.write(at_command)
        if flush:
            self.conn.write('\r')

        # Too small timeout will return immediately and got no data.
        # So here we should keep a short interval for reading and increase
        # it when not got the data we excpect.
        # If pyserial raise the timeoutException we need NOT hack this...

        # Get command execute results.
        # From 'AT' commands references, all commands will return:
        #   - 'OK' when executed successfully;
        #   - 'ERROR' when error occurs;
        # except for 'AT+CPIN?', 'AT+EXPKEY?', or incoming events.
        # We do NOT handle these kinds of commands or events, so we can simply
        # wait for 'OK' or 'ERROR', as the completion of command execution.
        self.total_timeout = self.max_timeout
        read_interval = self.min_timeout
        total_timeout = read_interval
        results = []
        while total_timeout < self.total_timeout:
            self.conn.setTimeout(total_timeout)
            result = self.conn.readlines()
            logging.debug('Timeout: %.2fs, Result lines: %d' % (
                total_timeout, len(result)))
            if (len(result) > 0):
                logging.debug('Result: %s' % result)
                results.extend(result)
                command_executed = False
                for s in result:
                    if 'OK' in s:
                        command_executed = True
                        break
                    elif 'ERROR' in s:
                        raise ModemError(results)
                if command_executed:
                    break
            total_timeout += read_interval
        logging.debug('Total time: %.2f' % total_timeout)
        if total_timeout >= self.total_timeout:
            raise TimeoutError(read_interval, self.total_timeout)

        logging.debug('Command results: %s' % results)
        return results

    def __del__(self):
        try:
            self.conn.close()
        except AttributeError:
            pass

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    import sys

    import conf

    modem = PDUModem(conf.DEBUG_PORT, conf.DEBUG_BAUD, conf.DEBUG_MIN_TIMEOUT)
    try:
        user_choice = raw_input('Send(s)? Read(r)? Quit(q)?\r\n')
        while (user_choice == 's' or user_choice == 'r'):
            if (user_choice == 's'):
                mobile = raw_input(
                    '\nInput a mobile phone number'
                    '(e.g 12345678901 or +8612345678901)'
                    '\npress Enter for default: %s: ' % 
                    conf.DEBUG_MOBILE)
                if not mobile:
                    mobile = conf.DEBUG_MOBILE
                msg = raw_input('\nInput message: ')
                msg_unicode = msg.decode(conf.DEBUG_ENCODING)
                print '\nSending to number: %s, with msg:\n\t%s\n' % (
                    mobile, msg_unicode)
                modem.send(mobile, msg_unicode)
                print '\nOK!\n'
            elif (user_choice == 'r'):
                print '\nRead SMS: '
                print '0-received unread'
                print '1-received read'
                print '2-stored unsent'
                print '3-stored sent'
                print '4-all, default'
                list_type = raw_input('\nInput list type (0-4): ')
                if not list_type in ('0', '1', '2', '3', '4'):
                    modem.close()
                    sys.exit(0)
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
            print '\nQuiting...'
            modem.close()
    except KeyboardInterrupt:
        print 'Exiting gracefully...'
        modem.close()
