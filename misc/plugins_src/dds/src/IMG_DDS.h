/*
 * Copyright (c) 2020
 *	Side Effects Software Inc.  All rights reserved.
 *
 * Redistribution and use of Houdini Development Kit samples in source and
 * binary forms, with or without modification, are permitted provided that the
 * following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 2. The name of Side Effects Software may not be used to endorse or
 *    promote products derived from this software without specific prior
 *    written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY SIDE EFFECTS SOFTWARE `AS IS' AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN
 * NO EVENT SHALL SIDE EFFECTS SOFTWARE BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
 * OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 *----------------------------------------------------------------------------
 * Read/Write raw files
 */

#ifndef __IMG_DDS__
#define __IMG_DDS__

#include <IMG/IMG_File.h>
#include <DirectXTex.h>

namespace DDS_File {
/// DDS image file format.  This class handles reading/writing the image.
/// @see IMG_DDSFormat
class IMG_DDS : public IMG_File
{
public:
     IMG_DDS();
    ~IMG_DDS();

    virtual int	 readScanline(int y, void *buf);

    virtual int	 create(const IMG_Stat &stat);
    virtual int	 writeScanline(int scan, const void *buf);
    virtual int	 closeFile();

private:

    bool m_write_flag;
    uint8_t* m_write_buffer;

    DirectX::ScratchImage* m_scratch_image;

    DXGI_FORMAT m_default_write_format;

    int      openFile(const char *fname) override;
};
}	// End of HDK_Sample namespace

#endif

