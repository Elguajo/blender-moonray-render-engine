---
title: Body Files
---
# Body Files

* Properly prototype all file static functions with usefully named parameters.

* Whenever possible, make variables and functions static or place them in an anonymous namespace to reduce namespace
collisions. For example:
```c++
// file : sort.cc
// both swap1 and swap2 are only visible in sort.cc
static void swap1(float& f1, float& f2) { /* ... */ }
namespace
{
void swap2(float& f1, float& f2) { /* ... */ }
}
```
* Avoid global variables.

* Constants and macros definitions should be at the top of the file or, when appropriate, in an include file.

* Multiple variables of the same data type may be declared on the same line if they correspond to fields of some logical
data structure.
```c++
    char *r, *g, *b;
    float x, y, z;
```

