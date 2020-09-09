cmake_minimum_required( VERSION 3.6 )

project( IMG_DDS )

# CMAKE_PREFIX_PATH must contain the path to the toolkit/cmake subdirectory of
# the Houdini installation. See the "Compiling with CMake" section of the HDK
# documentation for more details, which describes several options for
# specifying this path.
list( APPEND CMAKE_PREFIX_PATH "$ENV{HFS}/toolkit/cmake" )

# Locate Houdini's libraries and header files.
# Registers an imported library target named 'Houdini'.
find_package( Houdini REQUIRED )

set( library_name IMG_DDS )

# Code generation for the embedded DS file in SOP_Star.C.
# houdini_generate_proto_headers( FILES IMG_DDS.C )

# Add a library and its source files.
add_library( ${library_name} SHARED

    directx/DirectXTex.h
    directx/DirectXTexDDS.cpp
    directx/DirectXTexUtil.cpp
    directx/DirectXTexImage.cpp
    directx/DirectXTexConvert.cpp
    directx/DirectXTexMipmaps.cpp
    directx/DirectXTexCompress.cpp
    directx/BC.cpp
    directx/BC4BC5.cpp
    directx/BC6HBC7.cpp

    src/IMG_DDS.C
    src/IMG_DDS.h

)


# Link against the Houdini libraries, and add required include directories and
# compile definitions.
target_link_libraries( ${library_name} Houdini 
)

#link_directories( )
# Include ${CMAKE_CURRENT_BINARY_DIR} for the generated header.
target_include_directories( ${library_name} PRIVATE
    ${CMAKE_CURRENT_BINARY_DIR}
    directx
)

# Sets several common target properties, such as the library's output directory.
houdini_configure_target( ${library_name} INSTDIR $ENV{INSTDIR} )
