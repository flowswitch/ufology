#include <stdio.h>

#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>

//#include <Util/ConUtil.h>

#include "Ex200.h"

void main(int argc, char *argv[])
{
	if (argc!=3)
	{
		printf("Usage: %s <file> <size>\n", argv[0]);
		return;
	}

	unsigned size=0;
	sscanf(argv[2], "%x", &size);

        if (!UsbInit())
        {
          	return;
        }

        printf("Programmed:\n");
	printf("FW ID: %X\n", GetFirmwareId());
	printf("FW Revision: %X\n", GetFirmwareRevision());
	printf("FPGA ID: %08X\n", GetFpgaId());
	DownloadFw("ex200_fw.bix");
	DownloadFpga("ex200_fpga_notrig_80870617.bin", 0x80870617);
//	DownloadFpga("ex200_fpga_trig_A4665E22.bin ", 0xA4665E22);
	printf("\nLoaded:\n");
	printf("FW ID: %X\n", GetFirmwareId());
	printf("FW Revision: %X\n", GetFirmwareRevision());
	printf("FPGA ID: %08X\n", GetFpgaId());

//	Renumerate();
//	ResetEngine();
	ResetAcquisition();
        int hf = open(argv[1], O_CREAT | O_TRUNC | O_RDWR | O_BINARY, S_IWRITE);
        if (hf<0)
        {
        	goto close_exit;
	}
//	StartAcquisition(true);
	RxToFile(hf, size);
//	StopAcquisition();
//	FlushFifo();
	close(hf);

close_exit:
        UsbClose();
}
