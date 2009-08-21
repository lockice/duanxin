# -*- encoding: utf-8 -*-
#
# File name: pdu_msg.py
#
# SMS PDU mode message
#
# Written By: Chen Weiwei (Dave.Chen.ww@gmail.com)


class PDUMsg(object):
    """A PDU format SMS message"""

    def __init__(self, smsc, number, PID, DCS, DCS_desc,
                 text, length, date, received=True):
        """received = False indicates msg is transit"""
        self.smsc = smsc
        self.received = received
        self.number = number
        if date or received:
            self.date = date
        self.PID = PID
        self.DCS = DCS
        self.DCS_desc = DCS_desc
        self.length = length
        self.text = text

    def __unicode__(self):
        if self.received:
            out = "SMSC: " + self.smsc + "\nSender: " + self.number +\
                  "\nSend time: " + self.date + "\nTP_PID: " + self.PID +\
                  "\nTP_DCS: " + self.DCS + \
                  "\nTP_DCS-popis: " + self.DCS_desc + \
                  "\nUser Message: " + self.text + \
                  "\nLength: " + str(self.length)
        else:
            out = "SMSC: " + self.smsc + "\nTarget: " + self.number +\
                  "\nTP_PID: " + self.PID + "\nTP_DCS: " + self.DCS +\
                  "\nTP_DCS-popis: " + self.DCS_desc +\
                  "\nUser Message: " + self.text + \
                  "\nLength: " + str(self.length)

        return out

    def __str__(self):
        return self.__unicode__().encode('utf-8')
