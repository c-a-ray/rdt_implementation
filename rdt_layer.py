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

class SegmentData:
    def __init__(self, nextSeqNum, payload):
        self.nextSeqNum = nextSeqNum
        self.payload = payload


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
        self.seqNum = 0
        self.expectedSeqNum = 0
        self.seqNumsRecvd = []
        self.nextSeqNumToSend = 0
        # Add items as needed

    def setSendChannel(self, channel):
        self.sendChannel = channel

    def setReceiveChannel(self, channel):
        self.receiveChannel = channel

    def setDataToSend(self,data):
        self.dataToSend = data

    def getDataReceived(self):
        return self.dataReceived

    def processData(self):
        self.currentIteration += 1
        self.processSend()
        self.processReceiveAndSendRespond()

    def processSend(self):
        if len(self.dataToSend) == 0:
            return

        segmentSend = Segment()

        # You should pipeline segments to fit the flow-control window
        # The flow-control window is the constant RDTLayer.FLOW_CONTROL_WIN_SIZE
        # The maximum data that you can send in a segment is RDTLayer.DATA_LENGTH
        # These constants are given in # characters

        # Somewhere in here you will be creating data segments to send.
        # The data is just part of the entire string that you are trying to send.
        # The seqnum is the sequence number for the segment (in character number, not bytes)

        self.seqNum = self.nextSeqNumToSend
        self.nextSeqNumToSend = self.seqNum + self.DATA_LENGTH

        payload = self.dataToSend[self.seqNum:self.nextSeqNumToSend]
        segData = SegmentData(self.nextSeqNumToSend, payload)

        # Display sending segment
        segmentSend.setData(self.seqNum, segData)
        print("Sending segment: ", segmentSend.to_string())

        # Use the unreliable sendChannel to send the segment
        self.sendChannel.send(segmentSend)

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
        
        segmentAck = Segment()

        seqnumToSeg = {seg.seqnum: seg for seg in incomingBatch}

        nextSeqNumExpected = 0 if len(self.seqNumsRecvd) == 0 else max(
            self.seqNumsRecvd) + self.DATA_LENGTH

        orderedSegments = []
        while nextSeqNumExpected in seqnumToSeg.keys():
            nextExpectedSeg = seqnumToSeg[nextSeqNumExpected]
            orderedSegments.append(nextExpectedSeg)
            nextSeqNumExpected = nextExpectedSeg.payload.nextSeqNum

        for seg in orderedSegments:
            self.dataReceived = f'{self.dataReceived}{seg.payload.payload}'


        # ############################################################################################################ #
        # How do you respond to what you have received?
        # How can you tell data segments apart from ack segemnts?
        # print('processReceive(): Complete this...')

        # Somewhere in here you will be setting the contents of the ack segments to send.
        # The goal is to employ cumulative ack, just like TCP does...
        # acknum = "0"


        # ############################################################################################################ #
        # Display response segment
        # segmentAck.setAck(acknum)
        # print("Sending ack: ", segmentAck.to_string())

        # Use the unreliable sendChannel to send the ack packet
        # self.sendChannel.send(segmentAck)
