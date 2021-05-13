#ifndef _COMMANDS_H_INCLUDED
#define _COMMANDS_H_INCLUDED

//vendor requests:

//analyzer:
//	out 01 0000 0000 [0]	reset engine
#define VREQ_RESET_ENGINE	0x01

//	out 02 0/1  0000 [0]	start acquisition
#define VREQ_START_ACQUISITION	0x02

//	out 03 0000 0000 [0]	stop acquisition
#define VREQ_STOP_ACQUISITION	0x03

//	out 04 0000 0000 [0]	reset acquisition
#define VREQ_RESET_ACQUISITION	0x04

//	in  06 0000 0000 [4]	get sdram level
#define VREQ_GET_SDRAM_LEVEL	0x06

//	out 07 0000 0000 [0]	flush fifo
#define VREQ_FLUSH_FIFO		0x07

//	out 08 0000 0000 [len]	send check connection pattern
#define VREQ_SEND_CHECK_CONN_PATTERN	0x08

//	out 09 0000 0000 [len]	write trigger config	- делают 2 раза одно и то же
#define VREQ_WRITE_TRIGGER_CONFIG	0x09

//	in  10 0000 0000 [1]	read lut voltage level - result = (data/255.0)*3.3
#define VREQ_READ_LUT_VOLTAGE	0x10

//	in  11 0000 0000 [1]	check if analysis link is HS
#define VREQ_GET_LINK_SPEED	0x11

//hardware:
#define VREQ_WRITE_MEM		0xA0

//	in  B0 0000 0000 [8?]	get activated options
#define VREQ_GET_OPTIONS	0xB0

//	in  C1 0000 0000 [2]	get firmware id
#define VREQ_GET_FW_ID		0xC1

//	in  C2 0000 0000 [2]	get firmware revision
#define VREQ_GET_FW_REVISION	0xC2

//	out C3 0000 0000 [0]	renumerate
#define VREQ_RENUMERATE		0xC3

//	in  D0 0000 0000 [1]	get power supply state
#define VREQ_GET_POWER_STATE	0xD0

//	in  F0 0000 0000 [4]	get fpga id
#define VREQ_FPGA_GET_ID	0xF0

//	out F0 id_l id_h [0]	fpga download start
#define VREQ_FPGA_LOAD_START	0xF0

//	out F1 0000 0000 [len]	fpga download data, len<=0x1000, multiple
#define VREQ_FPGA_LOAD_DATA	0xF1

#endif
