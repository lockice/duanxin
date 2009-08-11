# -*- encoding: utf-8 -*-
#
# File name: SMS_PDU_Util.py
#
# SMS PDU mode utility
#
# Written By: Chen Weiwei (Dave.Chen.ww@gmail.com)
# Refator By: twinsant (twinsant@gmail.com)
#
# Code reference: Online PDU Encoder and Decoder, http://twit88.com/home/

import SMS_PDU_MSG

seven_bit_default = u'@£$¥èéùìòÇ\nØø\rÅå\u0394_\u03a6\u0393\u039b\u03a9\u03a0\u03a8\u03a3\u0398\u039e\u20ACÆæßÉ !"#¤%&\'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà'

class SMS_PDU_Util(object):
    """SMS PDU encoder and decoder"""

    # start of block, utilities : integer, binary, hex, string trans
    def HexToNum(self, hexNumberStr):
        """function to convert a Hex number into a 10-based number"""
        return int(hexNumberStr, 16)


    def SemiOctetToString(self, inp):
        """function to convert semi-octets to a string"""
        out = ''
        for i in range(0, len(inp), 2):
            temp = inp[i:i+2]
            out += temp[1] + temp[0]
        return out


    def IntToBin(self, intValue, bitSize):
        """function to convert an integer into a bit string"""
        def i2b(i):
            b = []
            while i:
                b.append(i%2)
                i >>= 1
            return b[::-1]

        bin = i2b(intValue)
        if (len(bin) < bitSize):
            for i in xrange(bitSize - len(bin)): bin.insert(0, 0)

        return ''.join([str(g) for g in bin])


    def BinToInt(self, binStr):
        """function to convert a bit string into an integer"""
        total = 0
        for i in range(len(binStr)):
            total <<= 1
            if (binStr[i] == '1'):
                total += 1

        return total


    def IntToHex(self, intValue, octetSize):
        """function to covert an integer into a hex octet"""
        size = octetSize*2
        hex_str = hex(intValue)[2:].upper()
        if (len(hex_str) > size):
            hex_str = hex_str[- size:]
        elif (len(hex_str) < size):
            insertion = '0'*(size - len(hex_str))
            hex_str = insertion + hex_str

        return hex_str


    def Get7Bit(self, character):
        """function to get default 7-bit character index"""
        for i in range(len(seven_bit_default)):
            if (seven_bit_default[i] == character):
                return i
        return 0;

    # end of block, utilities : integer, binary, hex, string trans


    # start of block, utilities : DCS
    def DCSTypeMeaning(self, tp_DCS):
        """function to get descriptions of specified DCS type"""
        tp_DCS_desc = tp_DCS
        pom_DCS = self.HexToNum(tp_DCS)

        if ((pom_DCS & 192) == 0):
            if (pom_DCS & 32):
                tp_DCS_desc = "Compressed Text\n"
            else:
                tp_DCS_desc = "Uncompressed Text\n"

            if (pom_DCS & 16):
                tp_DCS_desc += "No Class\n"
            else:
                tp_DCS_desc += "Class:" + str(pom_DCS & 3) + "\n"

            tp_DCS_desc += "Alphabet:"
            if ((pom_DCS & 12) == 0):
                tp_DCS_desc += "Default\n"
            elif ((pom_DCS & 12) == 4):
                tp_DCS_desc += "8bit\n"
            elif ((pom_DCS & 12) == 8):
                tp_DCS_desc += "UCS2(16)bit\n"
            elif ((pom_DCS & 12) == 12):
                tp_DCS_desc += "Reserved\n"

        elif ((pom_DCS & 192) == 64 or (pom_DCS & 192) == 128):
            tp_DCS_desc = "Reserved coding group\n"

        elif ((pom_DCS & 192) == 192):
            msg_waiting_group = pom_DCS & 0x30
            if (msg_waiting_group == 0):
                tp_DCS_desc = "Message waiting group\n"
                tp_DCS_desc += "Discard\n"
            elif (msg_waiting_group == 0x10):
                tp_DCS_desc = "Message waiting group\n"
                tp_DCS_desc += "Store Message. Default Alphabet\n"
            elif (msg_waiting_group == 0x20):
                tp_DCS_desc = "Message waiting group\n"
                tp_DCS_desc += "Store Message. UCS2 Alphabet\n"
            elif (msg_waiting_group == 0x30):
                tp_DCS_desc = "Data coding message class\n"
                if (pom_DCS & 0x4):
                    tp_DCS_desc += "Default Alphabet\n"
                else:
                    tp_DCS_desc += "8 bit Alphabet\n"

        return tp_DCS_desc


    def DCSBits(self, tp_DCS):
        """function to get bits size of specified DCS type"""
        alphabet_size = 7 # default bits size
        pom_DCS = self.HexToNum(tp_DCS)

        if ((pom_DCS & 192) == 0):
            if ((pom_DCS & 12) == 4):
                alphabet_size = 8
            elif ((pom_DCS & 12) == 8):
                alphabet_size = 16

        elif ((pom_DCS & 192) == 192):
            msg_waiting_group = pom_DCS & 0x30
            if (msg_waiting_group == 0x20):
                alphabet_size = 16
            elif (msg_waiting_group == 0x30):
                if ((pom_DCS & 0x4) == 0):
                    alphabet_size = 8;

        return alphabet_size

    # end of block, utilities : DCS


    # start of block, utilities : user msg string <=> PDU-coded string trans
    def GetUserMessage(self, pduString, strLength):
        """function to translate the input PDU-coded string to a "human readable" string
        for default 7 bit size"""
        byte_str = ''
        octets = []
        rests = []
        septets = []
        s = 1
        count = 0
        match_count = 0
        sms_msg = u''

        for i in range(0, len(pduString), 2):
            byte_str += self.IntToBin(self.HexToNum(pduString[i:i + 2]), 8)

        for i in range(0, len(byte_str), 8):
            octets.append(byte_str[i:i + 8])
            rests.append(octets[count][0:s % 8])
            septets.append(octets[count][s % 8:8])
            count += 1
            s += 1
            if (s == 8):
                s = 1

        for i in range(len(rests)):
            if (i % 7 == 0):
                if (i != 0):
                    sms_msg += seven_bit_default[self.BinToInt(rests[i-1])]
                    match_count += 1
                sms_msg += seven_bit_default[self.BinToInt(septets[i])]
                match_count += 1

            else:
                sms_msg += seven_bit_default[self.BinToInt(septets[i] + rests[i - 1])]
                match_count += 1

        if (match_count != strLength):
            sms_msg += seven_bit_default[self.BinToInt(rests[i - 1])]

        return sms_msg


    def GetUserMessage8(self, pduString, strLength):
        """function to translate the input PDU-coded string to a "human readable" string
        for 8 bit size"""
        sms_msg = u''
        for i in range(0, len(pduString), 2):
            sms_msg += unichr(self.HexToNum(pduString[i:i + 2]))
        return sms_msg


    def GetUserMessage16(self, pduString, strLength):
        """function to translate the input PDU-coded string to a "human readable" string
        for 16 bit size"""
        sms_msg = u''
        for i in range(0, len(pduString), 4):
            sms_msg += unichr(self.HexToNum(pduString[i:i + 4]))
        return sms_msg

    # end of block, utilities : user msg string <=> PDU-coded string trans


    def GetPDUMetaInfo(self, pduHexString):
        """function to get SMS meta information from PDU string"""
        PDUString = pduHexString
        start = 0

        # SMSC info
        SMSC_info_length = self.HexToNum(PDUString[0:2])
        SMSC_info = PDUString[2:2 + (SMSC_info_length*2)]
        SMSC_typeOfAddr = SMSC_info[0:2];
        SMSC_number = SMSC_info[2:2 + (SMSC_info_length*2)]

        if (SMSC_info_length != 0):
            SMSC_number = self.SemiOctetToString(SMSC_number)

            # if the number length is odd, remove the trailing 'F'
            if (SMSC_number[-1].upper() == 'F'):
                SMSC_number = SMSC_number[:-1]

            if (SMSC_typeOfAddr == '91'):
                SMSC_number = '+' + SMSC_number

        # SMS delivery info
        SMS_Delivery_start = (SMSC_info_length*2) + 2
        start = SMS_Delivery_start
        SMS_Delivery_1stOctet = PDUString[start:start + 2]
        start += 2

        if ((self.HexToNum(SMS_Delivery_1stOctet) & 0x03) == 1): # Transmit Msg
            # msg reference
            msg_ref = self.HexToNum(PDUString[start:start + 2])
            start += 2

            # target addr
            target_addr_length = self.HexToNum(PDUString[start:start + 2])
            if (target_addr_length % 2 != 0):
                target_addr_length += 1
            start += 2

            target_typeOfAddr = PDUString[start:start + 2]
            start += 2

            target_number = self.SemiOctetToString(PDUString[start:start + target_addr_length])

            if (target_number):
                if (target_number[-1].upper() == 'F'):
                    target_number = target_number[:-1]
                if (target_typeOfAddr == '91'):
                    target_number = '+' + target_number
                start += target_addr_length

            # type of PID
            tp_PID = PDUString[start:start + 2]
            start += 2

            # type of DCS
            tp_DCS = PDUString[start:start + 2]
            tp_DCS_desc = self.DCSTypeMeaning(tp_DCS)
            start += 2

            # validity period (optional)
            validity_period = self.HexToNum(PDUString[start:start + 2])
            start += 2

            # msg body, commonish block
            msg_length = self.HexToNum(PDUString[start:start + 2])
            start += 2

            bit_size = self.DCSBits(tp_DCS)

            user_data = "Undefined format"
            if (bit_size == 7):
                user_data = self.GetUserMessage(PDUString[start:], msg_length)
            elif (bit_size == 8):
                user_data = self.GetUserMessage8(PDUString[start:], msg_length)
            elif (bit_size == 16):
                user_data = self.GetUserMessage16(PDUString[start:], msg_length)

            user_data = user_data[:msg_length]
            if (bit_size == 16):
                msg_length /= 2
            # end of msg body commonish block

            out = SMS_PDU_MSG.SMS_PDU_MSG(SMSC_number, target_number,
                                          tp_PID, tp_DCS, tp_DCS_desc,
                                          user_data, msg_length, '', False)

        elif ((self.HexToNum(SMS_Delivery_1stOctet) & 0x03) == 0): # Receive Msg            
            # sender addr
            sender_addr_length = self.HexToNum(PDUString[start:start + 2])
            if (sender_addr_length % 2 != 0):
                sender_addr_length += 1
            start += 2

            sender_typeOfAddr = PDUString[start:start + 2]
            start += 2

            sender_number = self.SemiOctetToString(PDUString[start:start + sender_addr_length])

            if (sender_number):
                if (sender_number[-1].upper() == 'F'):
                    sender_number = sender_number[:-1]
                if (sender_typeOfAddr == '91'):
                    sender_number = '+' + sender_number
                start += sender_addr_length

            # type of PID
            tp_PID = PDUString[start:start + 2]
            start += 2

            # type of DCS
            tp_DCS = PDUString[start:start + 2]
            tp_DCS_desc = self.DCSTypeMeaning(tp_DCS)
            start += 2

            # time stamp
            time_stamp = self.SemiOctetToString(PDUString[start:start + 14])
            year = time_stamp[0:2]
            month = time_stamp[2:4]
            day = time_stamp[4:6]
            hour = time_stamp[6:8]
            minite = time_stamp[8:10]
            second = time_stamp[10:12]
            time_zone_value = self.HexToNum(time_stamp[12:14])
            sign = ''
            time_zone_offset = ''
            if (time_zone_value & 0x7f != 0):
                if (time_zone_value & 0x80):
                    sign = '-'
                    time_zone_value &= 0x7F
                time_zone_offset = str(time_zone_value/6)
            time_zone = 'GMT' + sign + time_zone_offset
            time_stamp = day + '/' + month +'/' + year + ' ' +\
                         hour + ':' + minite + ':' + second + ' ' + time_zone
            start += 14

            # msg body, commonish block
            msg_length = self.HexToNum(PDUString[start:start + 2])
            start += 2

            bit_size = self.DCSBits(tp_DCS)

            user_data = "Undefined format"
            if (bit_size == 7):
                user_data = self.GetUserMessage(PDUString[start:], msg_length)
            elif (bit_size == 8):
                user_data = self.GetUserMessage8(PDUString[start:], msg_length)
            elif (bit_size == 16):
                user_data = self.GetUserMessage16(PDUString[start:], msg_length)

            user_data = user_data[:msg_length]
            if (bit_size == 16):
                msg_length /= 2
            # end of msg body commonish block

            out = SMS_PDU_MSG.SMS_PDU_MSG(SMSC_number, sender_number,
                                          tp_PID, tp_DCS, tp_DCS_desc,
                                          user_data, msg_length, time_stamp)

        else:
            out = "Unhandled message"

        return out


    def MetaInfoToPDU(self, userMsg, targetNumber, smscNumber, bitSize):
        """function to translate user message into PDU-coded string
        this function """
        if (bitSize != 7 and bitSize != 8 and bitSize != 16):
            raise Exception('bitSize must be one of 7, 8, 16')
        if (isinstance(userMsg, unicode) == False):
            raise Exception('userMsg must be a Unicode string')

        # SMSC number
        SMSC_info_length = '00'
        SMSC_length = 0
        SMSC_number_format = ''
        SMSC_number = ''
        SMSC = ''
        smsc_number_str = str(smscNumber)
        if (smsc_number_str):
            SMSC_number_format = '92' # national
            if (smsc_number_str[0] == '+'):
                SMSC_number_format = '91' # international
                smsc_number_str = smsc_number_str[1:]
            elif (smsc_number_str[0] != '0'):
                SMSC_number_format = '91' # international

            if (len(smsc_number_str) % 2 != 0):
                smsc_number_str += 'F' # number length is odd, add trailing 'F'

            SMSC = self.SemiOctetToString(smsc_number_str)
            SMSC_length = (len(SMSC_number_format) + len(SMSC))/2

            # SMSC info length
            SMSC_info_length = str(SMSC_length)
            if (len(SMSC_info_length) == 1):
                SMSC_info_length = '0' + SMSC_info_length

        # fist submit octet
        First_submit_octet = '1100'

        # target number
        Target_number_length = '00'
        Target_number_format = '91'
        Target_number = ''
        target_number_str = str(targetNumber)
        if (target_number_str):
            Target_number_format = '92' # national
            if (target_number_str[0] == '+'):
                Target_number_format = '91' # international
                target_number_str = target_number_str[1:]
            elif (target_number_str[0] != '0'):
                Target_number_format = '91' # international

            Target_number_length = self.IntToHex(len(target_number_str), 1)
            if (len(target_number_str) % 2 != 0):
                target_number_str += 'F' # number length is odd, add trailing 'F'

            Target_number = self.SemiOctetToString(target_number_str)

        # type of PID
        TP_PID = '00'

        # type of DCS
        TP_DCS = '00' # Default
        if (bitSize == 8):
            TP_DCS = '04'
        elif (bitSize == 16):
            TP_DCS = '08'

        # validity period
        Valid_Period = 'AA'

        # user msgs
        # seperate msg into several pieces if too long
        max_length_per_msg = (bitSize == 16) and 70 or 140
        user_msgs = []
        pdu_msgs = []
        if (len(userMsg) <= max_length_per_msg):
            user_msgs.append(userMsg)
        else:
            max_length_per_msg -= 5 # add '(x/y)' before each seperated msg
            n = (len(userMsg) - 1) / max_length_per_msg + 1
            for i in range(n):
                begin = i * max_length_per_msg
                end = begin + max_length_per_msg
                if end > len(userMsg): end = len(userMsg)
                user_msgs.append(u'(%d/%d)' % (i+1, n) + userMsg[begin:end])

        # deal with each msg
        for msg in user_msgs:
            output = ''
            if (bitSize == 7):
                user_msg_size = self.IntToHex(len(msg), 1)
                octet_temp_1 = '';
                octet_temp_2 = '';
                for i in range(len(msg) + 1):
                    if (i == len(msg)):
                        if (octet_temp_2):
                            output += self.IntToHex(self.BinToInt(octet_temp_2), 1)
                        break

                    current = self.IntToBin(self.Get7Bit(msg[i]), 7)

                    if (i != 0 and i % 8 != 0):
                        octet_temp_1 = current[7 - i % 8:]
                        octet_current = octet_temp_1 + octet_temp_2
                        output += self.IntToHex(self.BinToInt(octet_current), 1)
                        octet_temp_2 = current[:7 - i % 8]
                    else:
                        octet_temp_2 = current[:7 - i % 8]

            elif (bitSize == 8):
                user_msg_size = self.IntToHex(len(msg), 1)
                for i in range(len(msg)):
                    output += self.IntToHex(ord(msg[i]), 1)

            elif (bitSize == 16):
                user_msg_size = self.IntToHex(len(msg)*2, 1)
                for i in range(len(msg)):
                    output += self.IntToHex(ord(msg[i]), 2)

            header = SMSC_info_length + SMSC_number_format + SMSC +\
                     First_submit_octet + Target_number_length +\
                     Target_number_format + Target_number +\
                     TP_PID + TP_DCS + Valid_Period + user_msg_size
            pdu = header + output
            length = len(pdu)/2 - SMSC_length - 1

            pdu_msgs.append((length, pdu))

        return pdu_msgs

