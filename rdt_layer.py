import time
from segment import Segment


# #################################################################################################################### #
# RDTLayer                                                                                                             #
#                                                                                                                      #
# Description:                                                                                                         #
# The reliable data transfer (RDT) layer is used as a communication layer to resolve issues over an unreliable         #
# channel.                                                                                                             #
#                                                                                                                      #
#                                                                                                                      #
# Notes:                                                                                                               #
# This file is meant to be changed.                                                                                    #
#                                                                                                                      #
#                                                                                                                      #
# #################################################################################################################### #

ACKED = 'ACKED'
SEG = 'seg'

class SegmentSendData:
    def __init__(self, data, nCharsToSend):
        self.payload = data
        self.nCharsToSend = nCharsToSend

class RDTLayer(object):
    DATA_LENGTH = 4 # in characters                     # The length of the string data that will be sent per packet...
    FLOW_CONTROL_WIN_SIZE = 15 # in characters          # Receive window size for flow-control
    sendChannel = None
    receiveChannel = None
    dataToSend = ''
    currentIteration = 0                                # Use this for segment 'timeouts'

    def __init__(self):
        self.sendChannel = None
        self.receiveChannel = None
        self.dataToSend = ''
        self.currentIteration = 0
        self.dataReceived = ''
        self.seqnum = 0
        self.nextSeqnum = self.DATA_LENGTH
        self.seqnumsACKed = {}
        self.segsReceived = {}
        self.acksRecvd = []
        self.timeout = False
        self.nCharsToSend = 0
        self.nCharsToRecv = 0
        # Add items as needed

    def setSendChannel(self, channel):
        self.sendChannel = channel

    def setReceiveChannel(self, channel):
        self.receiveChannel = channel

    def setDataToSend(self, data):
        self.dataToSend = data
        self.nCharsToSend = len(data)

    def getDataReceived(self):
        return self.dataReceived

    def startTimer(self):
        self.tStart = time.perf_counter()

    def checkForTimeout(self, timeoutLen):
        return time.perf_counter() - self.tStart > timeoutLen

    def findSmallestUnACKedSeg(self):
        ackedSeqnums = [seqnum for seqnum in self.seqnumsACKed.keys() if self.seqnumsACKed[seqnum][ACKED]]
        if len(ackedSeqnums) > 0:
            return self.seqnumsACKed[min(ackedSeqnums)][SEG]
        return 0

    def processData(self):
        self.currentIteration += 1
        self.processSend()
        self.processReceiveAndSendRespond()

    def processSend(self):
        if len(self.dataToSend) == 0:
            return

        segmentSend = Segment()

        if self.seqnum == 0:
            self.seqnum = self.nextSeqnum
        else:
            if self.checkForTimeout(2):
                self.seqnum = self.findSmallestUnACKedSeg()
            elif self.nextSeqnum not in self.seqnumsACKed.keys():
                return
            else:
                self.seqnum = self.nextSeqnum

        data = self.dataToSend[self.seqnum:self.nextSeqnum]
        segData = SegmentSendData(data, self.nCharsToSend)

        segmentSend.setData(self.seqnum, segData)
        print("Sending segment: ", segmentSend.to_string())

        self.seqnumsACKed[self.seqnum] = {
            ACKED: False,
            SEG: segmentSend,
        }

        # Use the unreliable sendChannel to send the segment
        self.sendChannel.send(segmentSend)
        self.startTimer()

        self.nextSeqnum = self.findSmallestUnACKedSeg() if self.checkForTimeout(
            2) else self.seqnum + self.DATA_LENGTH
        

    # ################################################################################################################ #
    # processReceive()                                                                                                 #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Manages Segment receive tasks                                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processReceiveAndSendRespond(self):
        incomingBatch = self.receiveChannel.receive()

        if len(incomingBatch) == 0:
            return

        if len(self.segsReceived) == 0 and hasattr(incomingBatch[0].payload, 'nCharsToSend'):
            self.nCharsToRecv = incomingBatch[0].payload.nCharsToSend

        incomingSegs = []
        for seg in incomingBatch:
            if seg.checkChecksum:
                if seg.seqnum == -1:
                    self.acksRecvd.append(seg.acknum)
                else:
                    self.segsReceived[seg.seqnum] = seg
                    incomingSegs.append(seg)

        for acknum in self.acksRecvd:
            self.seqnumsACKed[acknum - self.DATA_LENGTH][ACKED] = True

        if len(incomingSegs) == 0:
            return

        if len(self.segsReceived) == 0:
            maxSeqnumRecvd = 0
        else:
            maxSeqnumRecvd = max(self.segsReceived.keys())
            
        nextExpectedSeqnum = 0

        for seqnum in range(0, maxSeqnumRecvd + 1, self.DATA_LENGTH):
            if seqnum in self.segsReceived.keys():
                nextExpectedSeqnum = seqnum + self.DATA_LENGTH

        segmentAck = Segment()
        segmentAck.setAck(nextExpectedSeqnum)

        # Display response segment
        print("Sending ack: ", segmentAck.to_string())

        # Use the unreliable sendChannel to send the ack packet
        self.sendChannel.send(segmentAck)
