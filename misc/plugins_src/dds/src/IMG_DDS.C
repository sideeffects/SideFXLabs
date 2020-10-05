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

#include <sys/types.h>
#include <time.h>
#include <stdlib.h>
#include <stdio.h>
#include <limits.h>
#include <UT/UT_Endian.h>		// For byte swapping
#include <UT/UT_DSOVersion.h>
#include <UT/UT_SysClone.h>
#include <IMG/IMG_Format.h>
#include <IMG/IMG_FileOpt.h>
#include "IMG_DDS.h"
#include <IMG/IMG_Error.h>
#include <tools/henv.h>

#define MAGIC		0x1234567a
#define MAGIC_SWAP	0xa7654321		// Swapped magic number

wchar_t * UT_StringToWChar(const char *in_string)
{

    size_t newsize = strlen(in_string) + 1;
    wchar_t * wcstring = new wchar_t[newsize];
    size_t convertedChars = 0;
    mbstowcs_s(&convertedChars, wcstring, newsize, in_string, _TRUNCATE);

    return wcstring;

}

// helper function to get a format type from a string
DXGI_FORMAT DxFormatFromString(const char *format)
{
    DXGI_FORMAT dxi_format = DXGI_FORMAT_UNKNOWN;

    if (!strcmp(format, "DXGI_FORMAT_BC1_UNORM"))
	dxi_format = DXGI_FORMAT_BC1_UNORM;
    else if (!strcmp(format, "DXGI_FORMAT_BC2_UNORM"))
	dxi_format = DXGI_FORMAT_BC2_UNORM;
    else if (!strcmp(format, "DXGI_FORMAT_BC3_UNORM"))
	dxi_format = DXGI_FORMAT_BC3_UNORM;
    else if (!strcmp(format, "DXGI_FORMAT_BC4_UNORM"))
	dxi_format = DXGI_FORMAT_BC4_UNORM;
    else if (!strcmp(format, "DXGI_FORMAT_BC5_UNORM"))
	dxi_format = DXGI_FORMAT_BC5_UNORM;
    else if (!strcmp(format, "DXGI_FORMAT_R8G8B8A8_UNORM"))
	dxi_format = DXGI_FORMAT_R8G8B8A8_UNORM;
    else if (!strcmp(format, "DXGI_FORMAT_R16G16B16A16_FLOAT"))
	dxi_format = DXGI_FORMAT_R16G16B16A16_FLOAT;
    else if (!strcmp(format, "DXGI_FORMAT_R32G32B32A32_FLOAT"))
	dxi_format = DXGI_FORMAT_R32G32B32A32_FLOAT;

    return dxi_format;
}

// menu for the Save As Compression Options
static IMG_FileTag	theCompressionMenu[] = {
	IMG_FileTag("DEFAULT", "DEFAULT"),
	IMG_FileTag("DXGI_FORMAT_BC1_UNORM", "BC1/DXT1"),
	IMG_FileTag("DXGI_FORMAT_BC1_UNORM", "BC1/DXT1"),
	IMG_FileTag("DXGI_FORMAT_BC2_UNORM", "BC2/DXT3"),
	IMG_FileTag("DXGI_FORMAT_BC3_UNORM", "BC3/DXT5"),
	IMG_FileTag("DXGI_FORMAT_BC4_UNORM", "BC4"),
	IMG_FileTag("DXGI_FORMAT_BC5_UNORM", "BC5"),
	IMG_FileTag("DXGI_FORMAT_R8G8B8A8_UNORM", "R8G8B8A8"),
	IMG_FileTag("DXGI_FORMAT_R16G16B16A16_FLOAT", "R16G16B16A16"),
	IMG_FileTag("DXGI_FORMAT_R32G32B32A32_FLOAT", "R32G32B32A32"),
	
	IMG_FileTag(),
};


// Save As Options
static IMG_FileOption	theOptions[] = {
    IMG_FileOption(IMG_OPTION_STRING, "format", "DDS (Labs)",
					"DEFAULT", theCompressionMenu),
    IMG_FileOption(),
};

static IMG_FileOptionList	theOptionList(theOptions);

/// Custom image file format definition.  This class defines the properties of
/// the custom image format.
/// @see IMG_DDS
class IMG_DDSFormat : public IMG_Format {
public:
	     IMG_DDSFormat() {}
    virtual ~IMG_DDSFormat() {}

    virtual const char	*getFormatName() const;
    virtual const char	*getFormatLabel() const;
    virtual const char	*getFormatDescription() const;
    virtual const char	*getDefaultExtension() const;
    virtual IMG_File	*createFile()	 const;

    // Methods to determine if this is one of our recognized files.
    //	The extension is the first try.  If there are multiple matches,
    //	then we resort to the magic number (when reading)
    virtual int		 checkExtension(const char *filename) const;
    virtual int		 checkMagic(unsigned int) const;
    virtual IMG_DataType	 getSupportedTypes() const
	{ return IMG_DT_ALL; }
    virtual IMG_ColorModel       getSupportedColorModels() const
	{ return IMG_CM_ALL; }
    const IMG_FileOptionList *getOptions() const override;
    // Configuration information for the format
    virtual void		getMaxResolution(unsigned &x,
					         unsigned &y) const;

    virtual int			isReadRandomAccess() const  { return 0; }
    virtual int			isWriteRandomAccess() const { return 0; }
};

using namespace DDS_File;

const char *
IMG_DDSFormat::getFormatName() const
{
    // Very brief label (no spaces)
    return "DDS";
}

const char *
IMG_DDSFormat::getFormatLabel() const
{
    // A simple description of the format
    return "DDS (Labs)";
}

const char *
IMG_DDSFormat::getFormatDescription() const
{
    // A more verbose description of the image format.  Things you might put in
    // here are the version of the format, etc.
    return "DirectX image format";
}

const char *
IMG_DDSFormat::getDefaultExtension() const
{
    // The default extension for the format files.  If there is no default
    // extension, the format won't appear in the menus to choose image format
    // types.
    return "dds";
}

IMG_File *
IMG_DDSFormat::createFile() const
{
    return new IMG_DDS;
}

int
IMG_DDSFormat::checkExtension(const char *filename) const
{
    static const char	*extensions[] = { ".dds", ".DDS", 0 };
    return matchExtensions(filename, extensions);
}

int
IMG_DDSFormat::checkMagic(unsigned int magic) const
{
    // Check if we hit our magic number
    return (magic == MAGIC || magic == MAGIC_SWAP);
}

void
IMG_DDSFormat::getMaxResolution(unsigned &x, unsigned &y) const
{
    x = UINT_MAX;		// Stored as shorts
    y = UINT_MAX;
}

const IMG_FileOptionList *
IMG_DDSFormat::getOptions() const
{
    return &theOptionList;
}

IMG_DDS::IMG_DDS()
{
    m_write_flag = false;

    // format we use when we write from a ROP
    m_default_write_format = DXGI_FORMAT_BC1_UNORM;

    // this can be overriden from the environment variable
    const char *env_val = HoudiniGetenv("HOUDINI_DDS_DEFAULT_FORMAT");
    if (env_val)
    {
	    m_default_write_format = DxFormatFromString(env_val);
    }
}

IMG_DDS::~IMG_DDS()
{
    close();
}

// This function is called when we start to write a file to disk
int
IMG_DDS::create(const IMG_Stat &stat)
{
    myStat = stat;
    m_write_flag = true;

    m_write_buffer = new uint8_t[myStat.bytesPerImage()];
    int components = myStat.getPlane()->getComponentCount();

    // this is a current limitation on how the data is passed into the writing function, technically this can
    // be handled with some byte massaging if it becomes an issue
    if (components != 4)
    {
        imgError(IMG_ERROR_GENERIC, "DDS export requires an alpha channel to be present, even if it's solid white");
        m_write_flag = false;
        return false;
    }
    
    return true;
}

// this function gets called a few times, including when we're about finished writing to disk
int
IMG_DDS::closeFile()
{
    // If we're writing data, flush out the stream
    if (myOS) myOS->flush();	// Flush out the data

    // if this is being called after a create function, this write flag will be tripped
    // requesting us to write the file out
    if (m_write_flag)
    {
        DirectX::Image img;
        DirectX::ScratchImage scratch_image;

        img.width = myStat.getDataWidth();
        img.height = myStat.getDataHeight();

        // figure out the image depth
        IMG_DataType plane_data_type = myStat.getPlane()->getDataType();
        if (plane_data_type == IMG_FLOAT32)
            img.format = DXGI_FORMAT_R32G32B32A32_FLOAT;
        else if (plane_data_type == IMG_FLOAT16 || plane_data_type == IMG_HALF)
            img.format = DXGI_FORMAT_R16G16B16A16_FLOAT;
        else
            img.format = DXGI_FORMAT_R8G8B8A8_UNORM;


        img.rowPitch = myStat.bytesPerScanline();
        img.slicePitch = myStat.bytesPerImage();
        img.pixels = m_write_buffer;

        DirectX::Blob* blob = new DirectX::Blob();

        DXGI_FORMAT dxgi_format = m_default_write_format;

        // check if we're specifying the format in the option dialog of a Save As
        const char *    format;
        if (format = getOption("format"))
        {
	    dxgi_format = DxFormatFromString(format);
        }
	
	if (dxgi_format == DXGI_FORMAT_UNKNOWN)
	{
	    dxgi_format = m_default_write_format;
	}

        if (DirectX::IsCompressed(dxgi_format))
        {
            DirectX::Compress(img, dxgi_format, DirectX::TEX_COMPRESS_DEFAULT, DirectX::TEX_THRESHOLD_DEFAULT, scratch_image);
        }
        else
        {
	    if (img.format == dxgi_format)
	    {
		scratch_image.InitializeFromImage(img);
	    }
	    else 
	    {
		DirectX::Convert(img, dxgi_format, DirectX::TEX_FILTER_DEFAULT, DirectX::TEX_THRESHOLD_DEFAULT, scratch_image);
	    }

        }

        // trying to save directly to disk here will fail, because we have a lock on the system file,
        // so we save it to memory and then use the current lock to write into it.

        HRESULT hr = DirectX::SaveToDDSMemory(*scratch_image.GetImage(0,0,0), DirectX::DDS_FLAGS_NONE, *blob);
        if (FAILED(hr))
            return 0;

        // do the writing
        int bufferSize = blob->GetBufferSize();
        char* bufferPtr = (char*)blob->GetBufferPointer();
        myOS->write(bufferPtr, bufferSize);

        // remove the flag
        m_write_flag = false;
    }

    return 1;	// return success
}

// read a line of pixels into the buffer
int
IMG_DDS::readScanline(int y, void *buf)
{
    // fail if the image size is 0
    if (y >= myStat.getYres()) return 0;

    // fail if we don't have a dds image loaded
    if (m_scratch_image->GetImageCount() == 0)
	    return 0;

    // Houdini flips the image on the Y
    y = myStat.getYres()-1 - y;

    // Get the first mip of the first image
    const DirectX::Image* srcImage = m_scratch_image->GetImage(0, 0, 0);

    uint8* pixels = srcImage->pixels;
    size_t pitch = srcImage->rowPitch;

    // copy it into out internal buffer
    memcpy(buf, pixels + pitch * y, pitch);

    return 1;
}

// this gets called for every line when writing
int
IMG_DDS::writeScanline(int y, const void *buf)
{
    size_t pitch = myStat.bytesPerScanline();
    
    // Houdini flips the image on the Y
    y = myStat.getYres() - 1 - y;

    // accumulate the data that was read into the internal buffer m_write_buffer, to then be dumped to disk
    memcpy(m_write_buffer + pitch * y, buf, pitch);

    return 1;

}

// called when we load the file
int
IMG_DDS::openFile(const char *fname)
{

    m_scratch_image = new DirectX::ScratchImage();

    // load the file using the DirectX library
    HRESULT loadResult = DirectX::LoadFromDDSFile(UT_StringToWChar(fname), DirectX::DDS_FLAGS_NONE, nullptr, *m_scratch_image);
    if (FAILED(loadResult))
    	return 1;

    const DirectX::TexMetadata& textureMetaData = m_scratch_image->GetMetadata();
    DXGI_FORMAT textureFormat = textureMetaData.format;

    myStat.setResolution((uint32)textureMetaData.width, (uint32)textureMetaData.height);
    myStat.addDefaultPlane();
    
    myStat.getPlane()->setColorModel(IMG_RGBA);
    DirectX::ScratchImage *bcImage = new DirectX::ScratchImage();
    
    switch (textureMetaData.format)
    {
        // special case 16 and 32 bits as they are uncompressed and raw
        case DXGI_FORMAT_R16G16B16A16_FLOAT:
            myStat.getPlane()->setDataType(IMG_FLOAT16);
            break;

        case DXGI_FORMAT_R32G32B32A32_FLOAT:
            myStat.getPlane()->setDataType(IMG_FLOAT32);
            break;

        default:
            myStat.getPlane()->setDataType(IMG_UCHAR);

            // decompress and convert to a raw format
            if (DirectX::IsCompressed(textureFormat))
            {
                DirectX::Decompress(m_scratch_image->GetImages(), m_scratch_image->GetImageCount(), m_scratch_image->GetMetadata(), DXGI_FORMAT_UNKNOWN, *bcImage);
                m_scratch_image = bcImage;
            }

            DirectX::Convert(m_scratch_image->GetImages(), m_scratch_image->GetImageCount(), m_scratch_image->GetMetadata(), DXGI_FORMAT_R8G8B8A8_UNORM, DirectX::TEX_FILTER_DEFAULT, DirectX::TEX_THRESHOLD_DEFAULT, *bcImage);

            // stash it for later
            m_scratch_image = bcImage;

            break;
        }
    
    return 1;
}

////////////////////////////////////////////////////////////////////
//
//  Now, we load the format
//
////////////////////////////////////////////////////////////////////
void
newIMGFormat(void *)
{
    new IMG_DDSFormat();
}
