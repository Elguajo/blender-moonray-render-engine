---
title: Math Library
---
# Math Library

We use our own math library, **lib/common/math** in the **scene_rdl2** repo. For convenience we typically do the
following in our .cc files (but NEVER in our header files):
```c++
using namespace scene_rdl2::math;
```
so that math operators and constants use our own overloaded versions. This also provides several user-friendly math
types for simplifying ray tracing and shading calculations. For example, `Vec3f` is a `Vec3<float>`. In general, unless
the extra precision is required, floats are preferred over doubles for speed.
Basic examples:

```c++
// We use Vec3f to mean a vector of 3 floats
Vec3f N, I;

// Prefer using dot(N, I) instead of N.dot(I)
const float cosNI = dot(N, I);

// rcp(x) is faster than 1.0f / x when you don't need full precision
// reciprocals or divides.
const float invCosNI = rcp(cosNI);

// acos, sqrt etc. operate on both floats and doubles.
// See lib/common/math/Math.h for details
const float theta = acos(cosTheta);

// Make sure to use constants like 1.0f instead of 1.0 to avoid
// automatic casting back and forth between float and double
// in complex math expressions, which can make the code much slower
const float ai = 1.0f / (roughness * sqrt((1.0f - cosNI * cosNI) * (invCosNI * invCosNI)));
```
