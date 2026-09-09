---
title: Writing Map Shaders
---
# Writing Map Shaders
### Overview
Many of the topics covered in the general [Writing Shaders]({{ "/developer-reference/shaders/" | absolute_url }}) page apply to Map shaders, and it is advised that you look there first.

Map shaders produce color values and are typically bound to drive the value of an attribute on a Material, Displacement, or Volume shader, but they can also be rendered directly using MoonRay's
[Extra Aovs]({{ "/user-reference/how-to-guides/render-outputs/extra-aovs/" | absolute_url }}). They can be chained together with other Map shaders which can modify their output. These types of
shaders are sometimes referred to as "pattern generators", and while they can produce procedural patterns such as checker squares, polka dots, noise, gradients, etc. they can also read values
from primitive attributes, 2D image textures, volumetric data, etc.

A Map shader's job is to produce a color, given some set of inputs.

### Source files
There are typically 4 files that make up a Map shader's source:
* _\<ClassName\>.cc_
* _\<ClassName\>.ispc_
* _\<ClassName\>.json_
* CMakeLists.txt

The _.cc_ file is written in C++ and contains the class definition, the constructor/destructor, the `update()` function, and the static scalar `SampleFunc` function implementation.

The _.ispc_ file is written in ISPC and contains the vector `SampleFuncv` function implementation.  It is also common for the _.ispc_ source to contain any data structures or enumerations needed by the shader.

Attributes are declared in the _.json_ file via JSON.

### The sample() function
Each Map shader implements two static functions to support MoonRay's scalar and vector execution modes.  The `SampleFunc` and `SampleFuncv` function prototypes are defined in scene_rdl2's
[Types.h](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/Types.h).
                                                                                                
Map shaders inherit two protected function pointer members (`mSampleFunc` and `mSampleFuncv`) which they must set, typically in the constructor, to point to the two implementations which are named
`sample()` by convention.

### The moonray::shading::State
The shading [State](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/shading/State.h) provides the sample function with geometric data at the shading point.

### Related ISPC macros
The vectorized sample function (SampleFuncv) implementation is routinely followed by a call to the `DEFINE_MAP_SHADER` macro which is defined in [ShaderMacros.isph](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/shading/ispc/ShaderMacros.isph)

```
DEFINE_MAP_SHADER(<shader_name>, <sample_function_name>)
```

This macro provides enables profiling of the vectorized sample function and defines a function `ispc::<shader_name>_getSampleFunc()` which is used to get a function pointer to the ispc sample function
from c++ code.

### Examples
There are many Map shaders in the moonray and moonshine codebases that can provide concrete examples.

See the [CheckerboardMap](https://github.com/OpenMoonRay/moonray/tree/main/dso/map/CheckerboardMap) for a relatively simple example.
