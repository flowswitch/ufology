#include <windows.h>
#include <stdio.h>
#include <io.h>
#include <fcntl.h>
#include "cyapi.h"
#include "Commands.h"

//values from VisualUSB
#define NUM_READ_BUFS 		0x400
#define READ_XFER_SIZE		0x1000
#define READ_XFER_TIMEOUT	200

#define DATA_IN_EP	0x86

CCyUSBDevice *USBDevice;
CCyControlEndPoint *ep0 = 0;
CCyBulkEndPoint *ep_data_in = 0;

bool UsbInit()
{
  	USBDevice = new CCyUSBDevice(NULL);   // Create an instance of CCyUSBDevice
  	ep0 = USBDevice->ControlEndPt;

  	int eptCount = USBDevice->EndPointCount();
  	for(int i=0; i<eptCount;  i++)
  	{
      		if (USBDevice->EndPoints[i]->Address==DATA_IN_EP)
		{
        		ep_data_in = (CCyBulkEndPoint *) USBDevice->EndPoints[i];
		}
	}

        if (ep0==0)
        {
        	printf("Can't get EP0 !\n");
              	USBDevice->Close();
              	return false;
        }

        if (ep_data_in==0)
        {
              	printf("Can't get EP_DATA_IN !\n");
              	USBDevice->Close();
              	return false;
        }
        ep_data_in->SetXferSize(READ_XFER_SIZE);
        return true;
}

void UsbClose()
{
	ep_data_in->Abort();
	USBDevice->Close();
}

static bool WriteMem(unsigned short addr, const void *data, unsigned short len)
{
  ep0->Target   = TGT_DEVICE;
  ep0->ReqType  = REQ_VENDOR;
  ep0->ReqCode  = VREQ_WRITE_MEM;
  ep0->Value    = addr;
  ep0->Index    = 0;
  LONG bytesToSend =  len;
  return ep0->Write((PUCHAR)data,  bytesToSend);
}

int GetFirmwareId()
{
	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_GET_FW_ID;
        ep0->Value    = 0;
        ep0->Index    = 0;
        unsigned short data=0;
        LONG bytesToSend = 2;
        if (!ep0->Read((PUCHAR)&data,  bytesToSend))
        {
        	return -1;
	}
	return data;
}

int GetFirmwareRevision()
{
	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_GET_FW_REVISION;
        ep0->Value    = 0;
        ep0->Index    = 0;
        unsigned short data=0;
        LONG bytesToSend = 2;
        if (!ep0->Read((PUCHAR)&data,  bytesToSend))
        {
        	return -1;
	}
	return data;
}

bool Renumerate()
{
	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_RENUMERATE;
        ep0->Value    = 0;
        ep0->Index    = 0;
        unsigned short data=0;
        LONG bytesToSend = 0;
        return ep0->Write((PUCHAR)&data,  bytesToSend);
}

int GetFpgaId()
{
	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_FPGA_GET_ID;
        ep0->Value    = 0;
        ep0->Index    = 0;
        int data=0;
        LONG bytesToSend = 4;
        if (!ep0->Read((PUCHAR)&data,  bytesToSend))
        {
        	return -1;
	}
	return data;
}

bool ResetEngine()
{
	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_RESET_ENGINE;
        ep0->Value    = 0;
        ep0->Index    = 0;
        unsigned short data=0;
        LONG bytesToSend = 0;
        return ep0->Write((PUCHAR)&data,  bytesToSend);
}

bool ResetAcquisition()
{
	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_RESET_ACQUISITION;
        ep0->Value    = 0;
        ep0->Index    = 0;
        unsigned short data=0;
        LONG bytesToSend = 0;
        return ep0->Write((PUCHAR)&data,  bytesToSend);
}

bool StartAcquisition(bool b)
{
	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_START_ACQUISITION;
        ep0->Value    = b ? 1 : 0;
        ep0->Index    = 0;
        unsigned short data=0;
        LONG bytesToSend = 0;
        return ep0->Write((PUCHAR)&data,  bytesToSend);
}

bool StopAcquisition()
{
	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_STOP_ACQUISITION;
        ep0->Value    = 0;
        ep0->Index    = 0;
        unsigned short data=0;
        LONG bytesToSend = 0;
        return ep0->Write((PUCHAR)&data,  bytesToSend);
}

bool FlushFifo()
{
	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_FLUSH_FIFO;
        ep0->Value    = 0;
        ep0->Index    = 0;
        unsigned short data=0;
        LONG bytesToSend = 0;
        return ep0->Write((PUCHAR)&data,  bytesToSend);
}


//this is bix (not bin !) loader
bool DownloadFw(const char *fname)
{
        int hf = open(fname, O_RDONLY | O_BINARY);
        if (hf==-1)
                return false;
        unsigned char cmd = 1;
        if (!WriteMem(0xE600, &cmd, 1))
                return false;
        unsigned short len = filelength(hf);
        while(len)
        {
        	unsigned short addr;
        	read(hf, &addr, 2);
        	len-=2;
                unsigned len_b = (len>0x40) ? 0x40 : len;
                unsigned char buf[0x40];
                read(hf, buf, len_b);
                if (!WriteMem(addr, buf, len_b))
                        return false;
                len-=len_b;
        }
        close(hf);
        cmd = 0;
        if (!WriteMem(0xE600, &cmd, 1))
                return false;
        return true;
}

bool DownloadFpga(const char *fname, int id, bool force)
{
	if (!force)
	{
		if (GetFpgaId()==id)
		{
			return true;
		}
	}

        int hf = open(fname, O_RDONLY | O_BINARY);
        if (hf==-1)
                return false;
        unsigned len = filelength(hf);

	ep0->Target   = TGT_DEVICE;
  	ep0->ReqType  = REQ_VENDOR;
        ep0->ReqCode  = VREQ_FPGA_LOAD_START;
        ep0->Value    = id;
        ep0->Index    = id>>16;
        unsigned short data=0;
        LONG bytesToSend = 0;
        if (!ep0->Write((PUCHAR)&data,  bytesToSend))
        {
        	close(hf);
        	return false;
	}

        while(len)
        {
                unsigned len_b = (len>0x1000) ? 0x1000 : len;
                unsigned char buf[0x1000];
                read(hf, buf, len_b);

        	ep0->Target   = TGT_DEVICE;
          	ep0->ReqType  = REQ_VENDOR;
                ep0->ReqCode  = VREQ_FPGA_LOAD_DATA;
                ep0->Value    = 0;
                ep0->Index    = 0;
                LONG bytesToSend = len_b;
                if (!ep0->Write((PUCHAR)buf,  bytesToSend))
                {
                	close(hf);
                	return false;
        	}

                len-=len_b;
        }
        close(hf);
	
	if (GetFpgaId()!=id)
	{
		puts("FPGA id mismatch after download !");
		return false;
	}

        return true;
}

void RxToFileOld(int hf, __int64 total_len)
{
        unsigned char *buf[NUM_READ_BUFS];
        OVERLAPPED ovlp[NUM_READ_BUFS];
        PUCHAR ctx[NUM_READ_BUFS];
        bool first_run = true;
        buf[0] = new unsigned char[READ_XFER_SIZE*NUM_READ_BUFS];

        for(int i=0; i<NUM_READ_BUFS; i++)
        {
        	buf[i] = buf[0]+i*READ_XFER_SIZE;
          	ovlp[i].hEvent = CreateEvent(NULL, false, false, NULL);
        }

        while(total_len)
        {
        	__int64 cur_len = total_len;
        	int num_bufs = (cur_len+READ_XFER_SIZE-1)/READ_XFER_SIZE;
		if (num_bufs>NUM_READ_BUFS)
		{
			num_bufs = NUM_READ_BUFS;
		}
		//enqueue buffers
                for(int i=0; i<num_bufs; i++)
                {
          		LONG chunk_len = (cur_len>READ_XFER_SIZE) ? READ_XFER_SIZE : cur_len;
                	ctx[i] = ep_data_in->BeginDataXfer(buf[i], chunk_len, &(ovlp[i]));
                	cur_len-=chunk_len;
		}
/*		if (first_run)
		{
			StartAcquisition(true);
			first_run = false;
		}
*/
		//wait for completion and save data
                for(int i=0; i<num_bufs; i++)
                {
                	LONG chunk_len = READ_XFER_SIZE;
                       	ep_data_in->WaitForXfer(&(ovlp[i]), READ_XFER_TIMEOUT);
                       	ep_data_in->FinishDataXfer(buf[i], chunk_len, &(ovlp[i]), ctx[i]);
                       	write(hf, buf[i], chunk_len);
                       	total_len-=chunk_len;
                }
        }

        for(int i=0; i<NUM_READ_BUFS; i++)
        {
          	CloseHandle(ovlp[i].hEvent);
        }
        delete buf[0];
}

void RxToFile(int hf, __int64 total_len)
{
        unsigned char *buf[NUM_READ_BUFS];
        OVERLAPPED ovlp[NUM_READ_BUFS];
        PUCHAR ctx[NUM_READ_BUFS];
        bool first_run = true;
        buf[0] = new unsigned char[READ_XFER_SIZE*NUM_READ_BUFS];

        for(int i=0; i<NUM_READ_BUFS; i++)
        {
        	buf[i] = buf[0]+i*READ_XFER_SIZE;
          	ovlp[i].hEvent = CreateEvent(NULL, false, false, NULL);
        }

        //enqueue
        for(int i=0; i<NUM_READ_BUFS; i++)
        {
                ctx[i] = ep_data_in->BeginDataXfer(buf[i], READ_XFER_SIZE, &(ovlp[i]));
	}
	
	StartAcquisition(true);

	//data pump
	int i=0;
        while(true)
        {
        	if (ep_data_in->WaitForXfer(&(ovlp[i]), READ_XFER_TIMEOUT))
        	{
                	LONG chunk_len = READ_XFER_SIZE;
                       	ep_data_in->FinishDataXfer(buf[i], chunk_len, &(ovlp[i]), ctx[i]);
                       	write(hf, buf[i], chunk_len);

                       	ctx[i] = ep_data_in->BeginDataXfer(buf[i], READ_XFER_SIZE, &(ovlp[i]));

                       	total_len-=chunk_len;
                       	if (total_len<=0)
                       	{
                       		break;
			}

                       	i++;
                       	if (i==NUM_READ_BUFS)
                       	{
                       		i = 0;
			}
                }
        }

        StopAcquisition();
        FlushFifo();

        ep_data_in->Abort();
        for(int i=0; i<NUM_READ_BUFS; i++)
        {
                LONG chunk_len = READ_XFER_SIZE;
        	ep_data_in->FinishDataXfer(buf[i], chunk_len, &(ovlp[i]), ctx[i]);
          	CloseHandle(ovlp[i].hEvent);
        }
        delete buf[0];
}
