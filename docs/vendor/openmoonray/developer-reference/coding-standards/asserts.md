---
title: Asserts
---
# Asserts

* The use of the standard `assert()` macro referenced via `#include <cassert>` is allowed but discouraged.
The macros available via
```c++
    #include <scene_rdl2/lib/common/platform/Platform.h>
```
are preferred. This contains the following macro definitions:
* MNRY_ASSERT()
  Use this macro for assertions that you want compiled out of opt builds. This makes the macro appropriate for
  checks that potentially degrade performance. This macro throws an exception (`dwa::AssertFail`) when it fails,
  so it potentially terminates the application.
* MNRY_ASSERT_REQUIRE()
  Use this macro for assertions that you want active in both debug and opt builds. Make sure that the performance
  impact of the check is negligible. This macro throws an exception (`dwa::AssertFail`) when it fails, so it
  potentially terminates the application.
