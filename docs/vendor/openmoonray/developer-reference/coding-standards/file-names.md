---
title: File Names
---
# File Names

* C++ files have a .cc extension for source, and a .h extension for headers.

* ISPC files have a .ispc extension for source, and a .isph extension for headers.

* C++ file name should match the main class it defines. Classes with large implementations may be split among multiple
files. When this is done, name each file using the class name followed by an appropriate suffix (e.g. Image.h,
Image_file.h, Image_conversions.h).

* Library authors should provide a header with the same name as the library (e.g., ms.h). This header should include all
other exported header files.

* A header file that is not exported should either be the library name followed by _internal or be named to match a
particular body file.

* All command-line tools should have a main.cc file.

