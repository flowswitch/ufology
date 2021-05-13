#ifndef _EX200_H_INCLUDED
#define _EX200_H_INCLUDED

bool UsbInit();
void UsbClose();
bool DownloadFw(const char *fname);

int GetFirmwareId();
int GetFirmwareRevision();
bool Renumerate();
int GetFpgaId();
bool DownloadFpga(const char *fname, int id, bool force=false);

bool ResetEngine();
bool ResetAcquisition();
bool StartAcquisition(bool b=true);
bool StopAcquisition();
bool FlushFifo();

void RxToFile(int hf, __int64 total_len);


#endif
