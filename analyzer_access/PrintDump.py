#!/usr/bin/python
import os 
import sys
import struct

packet_time = 0

def outhex(s):
	for b in s:
		print "%02X" % (ord(b)),
	print ""

def ProcessPacket(pkt):
	global packet_time
	print "time %d" % (packet_time*100/6),
	
	flags = ord(pkt[0])
	if flags & 0x40:
		packet_time += struct.unpack("<H", pkt[1:3])[0]
		pos = 3
	else:
		packet_time += ord(pkt[1])
		pos = 2

	if flags & 0x80:
		ProcessLineState(flags)
	else:
		ProcessPidPacket(flags, pkt[pos:])				


def ProcessLineState(flags):
	state = flags & 0x0F
	if state==4:
		print "Power state changed to %d" % ((flags & 0x20)>>5)
	elif state==5:
		print "HS handshake, status %d" % ((flags & 0x30)>>4)
	elif state==0xE:
		print "state 0E: ",
		if flags & 0x10:
			print "skip"
		else:
			print "stop"
	else:
		LineStates = [ "0", "1", "2", "KeepAlive", "PowerState", "HSHandshake", "6", "7", "8", "stop 9", "stop A", "Trigger", "Bug C", "Bug D", "E", "F" ]
		print "Line state %s" % (LineStates[state])


def ProcessPidPacket(flags, pkt):
	speed = [ "speed 0", "HS", "speed 2", "speed 3" ]
	print "%s," % (speed[(flags & 0x30)>>4]),

	PID = [ "F0", "OUT", "ACK", "  DATA0", "PING", "SOF", "NYET", "  DATA2", "SPLIT", "IN", "NAK", "  DATA1", "PRE", "SETUP", "STALL", "  MDATA" ]
	pid = flags & 0x0F
	print PID[pid],

	IsToken = [ False, True, False, False, True, False, False, False, False, True, False, False, False, True, False, False ]
	if IsToken[pid]:
		print "dev%d:ep%d" % (ord(pkt[0]) & 0x7F, (ord(pkt[0])>>7) | ((ord(pkt[1])<<1) & 0x0E))
	elif pid==5: #SOF
		print "%d" % (struct.unpack("<H", pkt[0:2])[0] & 0x07FF)
	elif len(pkt)>0:
		outhex(pkt)
	else:
		print ""


################################ main ################################

if len(sys.argv)!=2:
	sys.exit("Usage: %s <dumpfile>" % (sys.argv[0]))

hf = open(sys.argv[1], "rb")
hf.seek(0, os.SEEK_END)
size = hf.tell()
hf.seek(0)

had_ec = False
packet = ""
for i in range(0, size):
	b = hf.read(1)
	cur_byte = struct.unpack("B", b)[0]
	if had_ec:
		if cur_byte!=0xEC and len(packet)!=0:
			ProcessPacket(packet)
			packet = ""
		had_ec = False
	elif cur_byte==0xEC:
		had_ec = True

	if not had_ec:
		packet = packet+b

hf.close()
