---
title: Scene RDL2 Attributes
---
# Scene RDL2 Attributes

Scenes ingested into MoonRay will typically use the rdla file format. This format is actually straight lua code in which
we define different types of SceneObjects, each with a specific set of attributes. For example, a bool attribute can be
set as follows:
```c++
["lights_visible_in_camera"] = true,
```
Here, `"lights_visible_in_camera"` is the attribute name. The convention for attribute names is lowercase letters and
numbers with underscores as word separators, or more formally, `[a-z][a-z0-9_]*`. New attributes added to rdla should
adhere to this convention, but legacy attribute names using spaces instead of underscores
(e.g. `"lights visible in camera"`) are supported through the use of aliases.

Some attributes take on enumerated integer values. A string can be supplied alongside each integer value for a more
descriptive way of denoting what each enumerated value represents. The convention for such strings is lowercase with
spaces. For example `"spiral square"` would be a valid enum string. Unlike attribute names, these are actual strings
and don't need to be valid C++ variable names, so `"quadratic b-spline"` would be a valid enum string also.

