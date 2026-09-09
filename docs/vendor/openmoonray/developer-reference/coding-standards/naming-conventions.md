---
title: Naming Conventions
---
# Naming Conventions

### Namespaces

All lowercase; words separated with underscores; no prefix (e.g., `pas`, `cdm_utils`).
Match the executable, library, or plug-in base name (e.g., `libfoo.so` --> `namespace foo`).

### Classes and C++ Structs

Mixed case; first letter uppercase (e.g., `SimpleEvent`, `QEdge`, `PointVector`).
Do not use a prefix.
If the class is derived and will include the base class name, then append the base class name
(e.g., `SimpleEvent` --> `TimedSimpleEvent`).
`struct` should only be used in C++ to describe very simple data structures that have no methods.

### Class Methods

Mixed case; first letter lowercase (e.g., `writeToSocket()`, `drawPolygon()`).
Simple accessors are get + the variable name, e.g. `scale = myObject.getScale();`
Simple mutators are set + the variable name, e.g. `myObject.setScale(scale);`
Methods that hand over the ownership of their result are take + the variable name
(e.g., `theObjPtr = theObjectContainer.takeMatch(theTarget);`)

### Class Instance Variables

Mixed case; always prefixed by m (e.g., `mQedgeId`, `mSocket`)

### Class Static Variables

Mixed case; always prefixed by s (e.g., `sQedgeHandle`, `sSingleton`)

### Local Variables and Function Parameters

Use mixed case with an initial lowercase (e.g., `index`, `polygonColor`, `userName`, `theCurrentMessage`, `aWidth`)

### Constants (via `#define`)

All uppercase; words separated by underscores. If not in a namespace or local to a body file, then prefixed with the
library name in all caps (e.g., `RADIX`, `ADB_ERROR_OK`).

### Enumeration Names

Mixed case; first letter uppercase (e.g., `Status`, `Color`)

### Enumeration Values

Same as constants; all uppercase; words separated by underscores (e.g., `FAILURE`, `SUCCESS`)

### C++ typedefs

Mixed case; first letter uppercase (e.g., `IntList`, `VectorRef`)
Do not use a prefix.

### Templates
Classes, methods, and functions follow the conventions of their non-template counterparts.

### Global C++ Variables

Mixed case; always prefixed by g (e.g., `gRegistry`).
In general, try to use class static data instead of globals in C++.

### Global C++ Functions

Mixed case; always prefixed by g (e.g., `gFunc()`).
In general, try to use class static members instead of global functions in C++.

### Booleans

When naming boolean functions and variables, use names that read as a condition. E.g:
```c++
if (isFull(bucket)) { ... }
if (bucketIsFull) { ... }
```

### Macros

Macros should be avoided unless there is no alternative. But if they are needed, they should be fully uppercase with
words separated by underscores. If not local to a body file, then they should be prefixed with the library name in all
caps (e.g., `WAD_SURFACE_COUNT(wad)`)
