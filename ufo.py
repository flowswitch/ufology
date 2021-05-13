#!/usr/bin/python3

__all__ = ["UfoReader", "Data", "Token", "Transfer", "Chirp", "Suspend", "Reset", "BusEvent"]

import os
from struct import unpack
from binascii import hexlify
import zlib
from struct import pack, unpack

from usb import pid_names

USBCRC16Table = (0, 0x0C0C1, 0x0C181, 0x140, 0x0C301, 0x3C0, 0x280, 0x0C241,
	0x0C601, 0x6C0, 0x780, 0x0C741, 0x500, 0x0C5C1, 0x0C481, 0x440,
	0x0CC01, 0x0CC0, 0x0D80, 0x0CD41, 0x0F00, 0x0CFC1, 0x0CE81, 0x0E40,
	0x0A00, 0x0CAC1, 0x0CB81, 0x0B40, 0x0C901, 0x9C0, 0x880, 0x0C841,
	0x0D801, 0x18C0, 0x1980, 0x0D941, 0x1B00, 0x0DBC1, 0x0DA81, 0x1A40,
	0x1E00, 0x0DEC1, 0x0DF81, 0x1F40, 0x0DD01, 0x1DC0, 0x1C80, 0x0DC41,
	0x1400, 0x0D4C1, 0x0D581, 0x1540, 0x0D701, 0x17C0, 0x1680, 0x0D641,
	0x0D201, 0x12C0, 0x1380, 0x0D341, 0x1100, 0x0D1C1, 0x0D081, 0x1040,
	0x0F001, 0x30C0, 0x3180, 0x0F141, 0x3300, 0x0F3C1, 0x0F281, 0x3240,
	0x3600, 0x0F6C1, 0x0F781, 0x3740, 0x0F501, 0x35C0, 0x3480, 0x0F441,
	0x3C00, 0x0FCC1, 0x0FD81, 0x3D40, 0x0FF01, 0x3FC0, 0x3E80, 0x0FE41,
	0x0FA01, 0x3AC0, 0x3B80, 0x0FB41, 0x3900, 0x0F9C1, 0x0F881, 0x3840,
	0x2800, 0x0E8C1, 0x0E981, 0x2940, 0x0EB01, 0x2BC0, 0x2A80, 0x0EA41,
	0x0EE01, 0x2EC0, 0x2F80, 0x0EF41, 0x2D00, 0x0EDC1, 0x0EC81, 0x2C40,
	0x0E401, 0x24C0, 0x2580, 0x0E541, 0x2700, 0x0E7C1, 0x0E681, 0x2640,
	0x2200, 0x0E2C1, 0x0E381, 0x2340, 0x0E101, 0x21C0, 0x2080, 0x0E041,
	0x0A001, 0x60C0, 0x6180, 0x0A141, 0x6300, 0x0A3C1, 0x0A281, 0x6240,
	0x6600, 0x0A6C1, 0x0A781, 0x6740, 0x0A501, 0x65C0, 0x6480, 0x0A441,
	0x6C00, 0x0ACC1, 0x0AD81, 0x6D40, 0x0AF01, 0x6FC0, 0x6E80, 0x0AE41,
	0x0AA01, 0x6AC0, 0x6B80, 0x0AB41, 0x6900, 0x0A9C1, 0x0A881, 0x6840,
	0x7800, 0x0B8C1, 0x0B981, 0x7940, 0x0BB01, 0x7BC0, 0x7A80, 0x0BA41,
	0x0BE01, 0x7EC0, 0x7F80, 0x0BF41, 0x7D00, 0x0BDC1, 0x0BC81, 0x7C40,
	0x0B401, 0x74C0, 0x7580, 0x0B541, 0x7700, 0x0B7C1, 0x0B681, 0x7640,
	0x7200, 0x0B2C1, 0x0B381, 0x7340, 0x0B101, 0x71C0, 0x7080, 0x0B041,
	0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
	0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
	0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
	0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
	0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
	0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
	0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
	0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040)


def USBCRC16(data):
	crc = 0xFFFF
	for b in data:
		b ^= crc
		crc = (crc>>8) ^ USBCRC16Table[b & 0xFF]
	return crc^0xFFFF


class Record(object):
	def __init__(self):
		self.t = 0
		self.l = 0
		self.flags = 0

	def fromFile(self, hf, l):
		ll, tt = unpack("BB", hf.read(2))
		if tt==0x80 or tt==0x00: # dword len
			tt = ll
			ll = unpack("<L", hf.read(4))[0]
		self.flags = tt & 0xC0
		self.t = tt & 0x3F
		self.l = ll

class Group(Record):
	pass

class RelatedGroup(Record):
	pass

class BusEvent(object):
	def __init__(self):
		self.time = -1

	def fromFile(self, hf, l):
		self.time = unpack("<Q", hf.read(8))[0]

class Comment(BusEvent):
	def __init__(self):
		BusEvent.__init__(self)
		self.end_time = -1

	def fromFile(self, hf, l):
		BusEvent.fromFile(self, hf, l)
		self.comment = hf.read(l-8).decode('utf-8')

	def __str__(self):
		return '# '+self.comment

class Keepalive(BusEvent):
	def __init__(self):
		BusEvent.__init__(self)

	def __str__(self):
		return "KEEP ALIVE"

class Reset(BusEvent):
	def __init__(self):
		BusEvent.__init__(self)
		self.end_time = -1

	def fromFile(self, hf, l):
		BusEvent.fromFile(self, hf, l)
		self.end_time = unpack("<Q", hf.read(8))[0]

	def __str__(self):
		return "RESET"

class Suspend(BusEvent):
	def __init__(self):
		BusEvent.__init__(self)
		self.end_time = -1

	def fromFile(self, hf, l):
		BusEvent.fromFile(self, hf, l)
		self.end_time = unpack("<Q", hf.read(8))[0]

	def __str__(self):
		return "SUSPEND"

class Power(BusEvent):
	def __init__(self):
		BusEvent.__init__(self)
		self.state = -1

	def fromFile(self, hf, l):
		BusEvent.fromFile(self, hf, l)
		self.state = unpack("<B", hf.read(1))[0]

	def __str__(self):
		if self.state==1:
			return "POWER ON"
		elif self.state==0:
			return "POWER OFF"
		else:
			return "POWER %d" % (self.state)

chirps = { 0 : 'OK',
	1 : 'Host timeout',
	2 : 'Device timeout',
	3 : 'Insufficient'}

class Chirp(BusEvent):
	def __init__(self):
		BusEvent.__init__(self)
		self.result = -1

	def fromFile(self, hf, l):
		BusEvent.fromFile(self, hf, l)
		self.result = unpack("<B", hf.read(1))[0]

	def __str__(self):
		return "CHIRP "+chirps.get(self.result, str(self.result))

class Transfer(object):
	def __init__(self):
		#Record.__init__(self)
		self.time = 0
		self.speed = 0
		self.pid = 0

	def fromFile(self, hf, l):
		#Record.fromFile(self, hf, l)
		self.time, self.speed, self.pid = unpack("<QBB", hf.read(10))

class Token(Transfer):
	def __init__(self):
		Transfer.__init__(self)
		self.dev = -1
		self.ep = -1

	def fromFile(self, hf, l):
		Transfer.fromFile(self, hf, l)
		d = unpack("<H", hf.read(2))[0]
		self.dev = d & 0x7F
		self.ep = (d>>7) & 0x0F

	def __str__(self):
		return "%s dev_%d ep_%d" % (pid_names[self.pid], self.dev, self.ep)

class Data(Transfer):
	def __init__(self):
		Transfer.__init__(self)
		self.data = None

	def fromFile(self, hf, l):
		Transfer.fromFile(self, hf, l)
		self.data = hf.read(l-12)
		hf.read(2) # drop CRC16
		
	def __str__(self):
		return pid_names[self.pid]+" "+self.data.hex()


class Handshake(Transfer):
	def __str__(self):
		return pid_names[self.pid]

# for dumping

class DummyRecord:

	def fromFile(self, hf, l):
		hf.seek(l, os.SEEK_CUR)

	def __str__(self):
		return ''

class DummyContainer:

	def fromFile(self, hf, l):
		#hf.seek(l, os.SEEK_CUR)
		pass

	def __str__(self):
		return ''

class TraceDataContainer(DummyContainer):
	pass

class TraceData(DummyContainer):
	pass

class TraceContainer(DummyContainer):
	pass

class SWInfoContainer(DummyContainer):
	pass

class TraceInfoContainer(DummyContainer):
	pass

class TraceSettings(DummyRecord):
	'''zLib-compressed text'''
	def __init__(self):
		self.text = ''

	def fromFile(self, hf, l):
		self.text = zlib.decompress(hf.read(l)).decode('utf-16')

	def __str__(self):
		return self.text		

class TraceSummary(DummyRecord):
	'''zLib-compressed XML'''
	def __init__(self):
		self.text = ''

	def fromFile(self, hf, l):
		self.text = zlib.decompress(hf.read(l)).decode('utf-16')

	def __str__(self):
		return self.text		

class UTF16Info(DummyRecord):
	def __init__(self):
		self.text = ''

	def fromFile(self, hf, l):
		self.text = hf.read(l).decode('utf-16')

	def __str__(self):
		return self.text		

class InfoVendor(UTF16Info):
	'''UTF-16 vendor name'''
	pass


class InfoVendorURL(UTF16Info):
	'''UTF-16 vendor URL'''
	pass

class InfoVendorEmail(UTF16Info):
	'''UTF-16 vendor e-mail'''
	pass

class InfoSoftware(UTF16Info):
	'''UTF-16 software name'''
	pass

class InfoSwVersion(DummyRecord):
	'''u16 l, u16 ml, u16 mh, u16 h'''
	def __init__(self):
		self.ver = (0,0,0,0)

	def fromFile(self, hf, l):
		self.ver = unpack('<HHHH', hf.read(l))

	def __str__(self):
		return '%d.%d.%d.%d' % (self.ver[3], self.ver[2], self.ver[1], self.ver[0])

class InfoSupportEmail(UTF16Info):
	'''UTF-16 support e-mail'''
	pass

class Info3A(DummyRecord):
	pass

class Info3B(DummyRecord):
	def __init__(self):
		self.data = b''

	def fromFile(self, hf, l):
		self.data = hf.read(l)

	def __str__(self):
		return self.data.hex().upper()

class Container3C(DummyContainer):
	pass

class NullTag(DummyRecord):
	'''Empty terminator'''
	pass

class EncryptedText(DummyRecord):
	def __init__(self):
		self.text = ''

	def fromFile(self, hf, l):
		data = hf.read(l)
		t = b''
		for i in range(0, len(data), 2):
			t += pack('B', data[i]+1-data[i+1])
		self.text = t.decode('ascii')

	def __str__(self):
		return self.text		
	
class InfoAnalyzerSN(EncryptedText):
	pass

class InfoAnalyzerModel(EncryptedText):
	pass

class InfoEncSwVersion(EncryptedText):
	pass

class InfoOSVersion(EncryptedText):
	pass

class Info3D(DummyRecord):
	def __init__(self):
		self.data = 0

	def fromFile(self, hf, l):
		self.data = unpack('<H', hf.read(l))[0]

	def __str__(self):
		return '%04X' % (self.data)

class InfoAnalyzerModel(DummyRecord):
	def __init__(self):
		self.model = 0

	def fromFile(self, hf, l):
		self.model = unpack('<B', hf.read(l))[0]

	def __str__(self):
		return '%d' % (self.model)

class InfoAnalyzerFeatures(DummyRecord):
	def __init__(self):
		self.features = 0

	def fromFile(self, hf, l):
		self.features = unpack('<Q', hf.read(l))[0]

	def __str__(self):
		return '%016X' % (self.features)

class InfoHCI(DummyRecord):
	def __init__(self):
		self.hcis = (0,0,0)

	def fromFile(self, hf, l):
		self.hcis = unpack('<LLL', hf.read(l))

	def __str__(self):
		return 'UHCI: %d, OHCI: %d, EHCI: %d' % (self.hcis)


##############################################################################

CLASS_UNI = 0x00
CLASS_APP = 0x40
CLASS_CTX = 0x80
CLASS_PRIV = 0xC0

uni_tag_map = {
	0x00 : TraceDataContainer,
	0x01 : TraceData,
	0x07 : RelatedGroup,
	0x32 : TraceContainer,
	0x3A : Info3A,
	0x3E : TraceInfoContainer,
	0x3F : NullTag,
}

app_tag_map = { 
	0x00 : InfoAnalyzerSN,
	0x01 : InfoAnalyzerModel,
	0x02 : InfoAnalyzerFeatures,
	0x03 : InfoEncSwVersion,
	0x04 : InfoOSVersion,
	0x05 : TraceSettings,
	0x06 : TraceSummary,
	0x07 : InfoHCI,
	0x08 : Token,
	0x09 : Data,
	0x0A : Handshake,
	0x14 : Reset,
	0x15 : Suspend,
	0x16 : Keepalive,
	0x17 : Power,
	0x18 : Chirp,
	0x31 : Comment,
	0x34 : InfoVendor,
	0x35 : InfoVendorURL,
	0x36 : InfoVendorEmail,
	0x37 : InfoSoftware,
	0x38 : InfoSwVersion,
	0x39 : InfoSupportEmail,
	0x3B : Info3B,		
	0x3D : Info3D,
}

ctx_tag_map = {
}

priv_tag_map = {
	0x07 : Group,
	0x33 : SWInfoContainer,		
	0x3C : Container3C,
}

tag_map = {
	CLASS_UNI : uni_tag_map,
	CLASS_APP : app_tag_map,
	CLASS_CTX : ctx_tag_map,
	CLASS_PRIV : priv_tag_map }

UFO_MAGIC = b'Ellisys Visual USB Data File\x00\x0D\x0A\x1A'
UFO_GUID = b'\x81\xC5\x66\xA7\xFB\x87\xD6\x46\xA7\x4F\x5F\x2F\xF6\xD0\x56\xE2'

class UfoReader(object):
	def __init__(self, fname, dump=False):
		self.dump = dump
		self.hfi = open(fname, "rb")
		hdr = self.hfi.read(0x50)
		magic, uuid, type_guid, trace_size, rsvd44, rsvd48, n_extra, rsvd4C, crc = unpack('<32s16s16sLLHHHH', hdr)
		if magic!=UFO_MAGIC or type_guid!=UFO_GUID:
			self.hfi.close()
			raise Exception("Not an UFO file")
		crc_calc = USBCRC16(hdr[0:0x4E])
		if crc!=crc_calc:
			print("Header CRC mismatch !\nCalculated: %04X\nStored: %04X" % (crc_calc, crc))
		# extra data beyond Trace is raw, no TLVs
		self.extra_start = trace_size
		self.extra_end = os.path.getsize(fname)		

		# check for outer TRACE CONTAINER tag
		# contains: SWInfo, TraceDataContainer, some small tags, TraceSettings, TraceSummary, Null
		t, l, f = self.get_tlf()
		if t!=0x32:
			self.hfi.close()
			raise Exception('No TRACE CONTAINER')
		# end of TLVs beyoud TraceDataContainer
		self.trace_extra_end = self.hfi.tell()+l

		# check for SWInfo (TLVs of strings inside)
		t, l, f = self.get_tlf()
		if t!=0x33:
			self.hfi.close()
			raise Exception('No INFO')
		self.info_start = self.hfi.tell()
		self.info_end = self.info_start+l
		# skip it
		self.hfi.seek(l, os.SEEK_CUR)

		# check outer TRACE DATA CONTAINER tag
		# contains TraceData 
		t, l, f = self.get_tlf()
		if t!=0x00:
			self.hfi.close()
			raise Exception('No TRACE DATA CONTAINER')
		# TLVs beyond TraceDataContainer - some small tags, TraceSettings, TraceSummary, Null
		self.trace_extra_start = self.hfi.tell()+l
		

		# check inner TRACE DATA tag
		# contains trace records
		t, l, f = self.get_tlf()
		if t!=0x01:
			self.hfi.close()
			raise Exception('No TRACE DATA')

		self.trace_start = self.prev_pos = self.hfi.tell()
		self.trace_end = self.prev_pos+l
		self.t = -1
		self.l = -1
		self.cache = None

	def get_tlf(self, pos=None):
		if pos!=None:
			self.hfi.seek(pos)
		l, t = unpack("<BB", self.hfi.read(2))
		if t==0x80 or t==0x00: # dword len
			t = l
			l = unpack("<L", self.hfi.read(4))[0]
		f = t & 0xC0
		t = t & 0x3F
		if self.dump:
			pos = self.hfi.tell()
			if t in tag_map[f]:
				t_name = tag_map[f][t].__name__
				print('%08X: F=%02X T=%02X %s [%X] -%X' % (pos, f, t, t_name, l, pos+l))
			else:
				print('%08X: F=%02X T=%02X [%X] -%X' % (pos, f, t, l, pos+l))
		return t, l, f

	####### Non-trace data dumping #########

	def DumpSwInfo(self):
		self.hfi.seek(self.info_start)
		while self.hfi.tell()<self.info_end:
			t, l, f = self.get_tlf()
			if t in tag_map[f]:
				cls = tag_map[f][t]
				rec = cls()
				rec.fromFile(self.hfi, l)
				print(rec)
			else:
				v = self.hfi.read(l)
				print("{", v.hex().upper(), "}")

	def DumpTraceInfo(self):
		self.hfi.seek(self.trace_extra_start)
		while self.hfi.tell()<self.trace_extra_end:
			t, l, f = self.get_tlf()
			if t in tag_map[f]:
				cls = tag_map[f][t]
				rec = cls()
				rec.fromFile(self.hfi, l)
				print(rec)
			else:
				v = self.hfi.read(l)
				print("{", v.hex().upper(), "}")

	####### TraceData read functions #######

	def available(self):
		return self.hfi.tell()<self.trace_end

	def get(self):
		if self.cache:
			rec = self.cache
			self.cache = None
			return rec
		pos = self.hfi.tell()
		if pos>=self.trace_end:
			return None

		t, l, f = self.get_tlf()

		if t==0x07 and f in (CLASS_UNI, CLASS_PRIV): # group
			recs = []
			end_pos = self.hfi.tell()+l
			while self.hfi.tell()<end_pos:
				recs.append(self.get())
			if self.hfi.tell()!=end_pos:
				raise Exception("Group misalign !")
			return recs
		else:
			if t in tag_map[f]:
				cls = tag_map[f][t]
				rec = cls()
				rec.fromFile(self.hfi, l)
				return rec
			else:
				raise Exception("Unsupported tag %02X" % (t))

	def put(self, rec):
		self.cache = rec	

	def close(self):
		self.hfi.close()


if __name__=="__main__":
	import sys

	if len(sys.argv)!=2:
		sys.exit("Usage: "+sys.argv[0]+" <file.ufo>")

	reader = UfoReader(sys.argv[1], dump=True)

	
	print("------- SW Info -------")
	reader.DumpSwInfo()

	print("------- Trace Data -------")
	reader.hfi.seek(reader.trace_start)
	while reader.available():
		print("%08X: " % reader.hfi.tell(), end='')
		rec = reader.get()
		if isinstance(rec, list):
			print("{")
			for r in rec:
				print("\t", r)
			print("}")
		else:
			print(rec)

	print("------- Trace Info -------")
	reader.DumpTraceInfo()

	reader.close()
