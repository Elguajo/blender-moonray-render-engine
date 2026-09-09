---
title: Header Files
---
# Header Files

* Ideally, headers should only describe the interface and not contain the implementation of the class, with a few
exceptions:
  + the class data members;
  + simple accessor/mutator (eg. get/set) function members;
  + member functions that use the "inline" keyword for performance reasons, assuming that profiling shows a benefit;
  + template members.

* The remaining function members and static function definitions should be placed in the accompanying .cc file.
For classes that are part of a public API the PIMPL pattern is recommended to keep the implementation completely out
of the header and in the .cc file.

* All header files should use `#pragma once` to prevent multiple inclusions. This is generally preferred over the use of
include guards using `#ifndef`/`#define`/`#endif`. The only exception is when the compiler outputs errors arising from
multiply included files. In that case, use include guards with this format:
```c++
    #ifndef <NAME>_H
    #define <NAME>_H
    ...
    #endif
```
* In class definitions, list public, then protected, then private members. List methods before variables.

* Fully prototype all functions, use descriptive naming for each parameter.

* Do not take advantage of indirect inclusion of header files - every file should explicitly include the headers it
needs, and not rely on other headers to bring them in indirectly. However, you may break this rule for headers that are
purely internal to a library.

* Do not use anonymous namespaces in header files, except when defining functions in the global namespace.

