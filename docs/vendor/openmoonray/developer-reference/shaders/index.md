---
title: Writing Shaders
---
# Writing Shaders
This page covers some general information about writing plug-ins (aka. _shaders_, _DSO's_, _procedurals_)
for MoonRay. At the time of this writing, MoonRay includes about 163 plug-ins, (see [scene-objects]({{ "/user-reference/scene-objects" | absolute_url }}))
but additional plug-ins can be authored to extend MoonRay's functionality.

Probably the best way to quickly understand what is required to write a new plug-in of a given
type is to have a look at the source code for existing plug-ins of that type. This page covers some
of the general topics that are common to all MoonRay plugin types. See the links at the bottom of this page 
for type-specific information.

The [_moonray_](https://github.com/OpenMoonRay/moonray/tree/main/dso),
[_moonshine_](https://github.com/OpenMoonRay/moonshine/tree/main/dso) and
[_moonshine_usd_](https://github.com/OpenMoonRay/moonshine_usd/tree/main/dso) repositories all
contain various plug-ins which can be referenced as examples and provide more information than can be
conveyed in this document.

----
## Plug-in Types
MoonRay supports several types of plug-ins. Each plug-in derives from one of the scene_rdl2 types and
implements its corresponding interface.

For some plug-in types a public API (using this term loosely) is provided which allows for authoring new plug-ins using only
the installed public header files. This allows them to be built separately from MoonRay itself --
in another repository, for example. For other types, a public API has not yet been created.
It is still possible to author new plug-ins of these types (this is open source, after all), but for
now it will be necessary to build them alongside MoonRay inside the _moonray_ source repo codebase.

|Type| Derives from | Has Public API?|
|------------|---------------|
|Camera|[scene_rdl2::rdl2::Camera](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/Camera.h)|no|
|Displacement|[scene_rdl2::rdl2::Displacement](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/Displacement.h)|yes|
|DisplayFilter|[scene_rdl2::rdl2::DisplayFilter](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/DisplayFilter.h)|yes|
|Geometry|[scene_rdl2::rdl2::Geometry](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/Geometry.h)|yes|
|Light|[scene_rdl2::rdl2::Light](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/Light.h)|no|
|LightFilter|[scene_rdl2::rdl2::LightFilter](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/LightFilter.h)|no|
|Map|[scene_rdl2::rdl2::Map](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/Map.h)|yes|
|Material|[scene_rdl2::rdl2::Material](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/Material.h)|yes|
|NormalMap|[scene_rdl2::rdl2::NormalMap](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/NormalMap.h)|yes|
|VolumeShader|[scene_rdl2::rdl2::VolumeShader](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/VolumeShader.h)|no|

All plug-in types are authored as C++ classes, but some plug-in types also include functions that
are written in ISPC.

----
## Naming Your Plug-in

Our convention is to append the plug-in type to the class name to make it easy to identify
what type of SceneObject it is when it appears in an RDLA file. For example, the class for
a new Map shader might be named `ZebraMap`, and the class for a new Light shader might be named
`TorusLight`.  This makes it possible to infer the plug-in type from the class name.  In an
RDLA file they might appear as:

```lua
-- scene.rdla
ZebraMap("/some/name/my_zebra") {
    ["num_stripes"] = 42,
}

TorusLight("/some/name/foo_17") {
    ["inner_radius"] = 4.2,
    ["outer_radius"] = 5.2,
}
```

----
## The Plug-in's Files and Directory Structure
Most MoonRay plug-ins comprise several source files, as follows:

|File|Required|Purpose|
|----|-------|
| _\<ClassName\>.cc_ | always | The C++ source file which defines the class and scalar functions |
| _\<ClassName\>.ispc_ |for some plug-in types | An ISPC source file which implements one or more vector functions |
| _attributes.cc_ or _\<ClassName\>.json_ | always | A C++ or JSON file (dependending on plug-in type) which defines a list of user-facing attributes |
| _CMakeLists.txt_ | always | Used to build the plug-in with CMake |
| _SConscript_ | never | Used only for legacy internal DWA builds, not needed for new plug-ins. Existing _SConscript_ files will be removed in a later release |

All of the above files should be placed within their own source directory to satisfy the one-dso-per-directory
requirement of the current build system.

For example, the source files for a new "Zebra" map shader might be:

```bash
moonray/dso/map/ZebraMap/
├── ZebraMap.cc
├── ZebraMap.ispc
├── ZebraMap.json
└── CMakeLists.txt
```

----
## Defining the Plug-in's Attributes
Attributes are how a SceneClass exposes control to the end-user.  Attributes come in many types, including:

`Bool Int Long Float Double String Rgb Rgba Vec2f Vec2d Vec3f Vec3d Vec4f Vec4d Mat4f Mat4d BoolVector`
`IntVector LongVector FloatVector DoubleVector StringVector RgbVector RgbaVector Vec2fVector Vec2dVector`
`Vec3fVector Vec3dVector Vec4fVector Vec4dVector Mat4fVector Mat4dVector SceneObject* SceneObjectVector`
`SceneObjectIndexable SceneObjectSet ConstSceneObjectSet`

Each attribute can have a default value, a label to use for display in a UI, a useful comment to describe its
purpose to the user, as well as one or more flags that affect their behavior, eg. `FLAGS_BINDABLE FLAGS_BLURRABLE FLAGS_ENUMERABLE FLAGS_FILENAME` etc.

Attributes can also have additional arbitrary metadata associated with them to control where and how they appear or
behave when displayed in a user-interface, or for any other purpose, really.

The build system expects a SceneClass's attributes to be declared in a C++ file named `attributes.cc` _or_
in a JSON file named `<ClassName>.json`, depending on the plug-in type.

The table below shows where the attributes are defined for each plug-in type:

|Type|Attributes file|
|----|--------------|
|Camera|attributes.cc|
|Displacement|\<ClassName\>.json|
|DisplayFilter|\<ClassName\>.json|
|Geometry|attributes.cc|
|Light|attributes.cc|
|LightFilter|attributes.cc|
|Map|\<ClassName\>.json|
|Material|\<ClassName\>.json|
|NormalMap|\<ClassName\>.json|
|VolumeShader|attributes.cc|

For plug-in types that use JSON to declare their attributes an extra step in the build process reads the JSON and
automatically generates the `attributes.cc` file at build time. In either case, the `attributes.cc` file should
ultimately be included near the top of the plug-in's `<ClassName>.cc` file.

```cpp
// ClassName.cc
#include "attributes.cc"
```

### The attributes.cc file
This file declares the attributes for the DSO type, including their default values and any metadata. It contains no other
code than RDL2 attribute declarations. It consists of two sections (the declarations and the definitions), delimited by 3
macros. A bare bones `attributes.cc` file might look like this:

```cpp
// attributes.cc
#include <scene/rdl2/rdl2.h>
  
using namespace arras;
  
RDL2_DSO_ATTR_DECLARE
  
    rdl2::AttributeKey<rdl2::Bool>  attrShowLid;
    rdl2::AttributeKey<rdl2::Float> attrSpoutRadius;
  
RDL2_DSO_ATTR_DEFINE(rdl2::Geometry)
  
    attrShowLid =
        sceneClass.declareAttribute<rdl2::Bool>("show_lid", true);

    attrSpoutRadius =
        sceneClass.declareAttribute<rdl2::Float>("spout_radius", 1.0f);
  
RDL2_DSO_ATTR_END
```

In the declare section, you simply declare an `AttributeKey<T>` for each attribute. By convention, we prefix these with "attr"
to avoid name conflicts. They will exist as variables in an anonymous namespace within our `MyTeapotGeometry.cc` file. You are in a
namespace scope, so you can't write arbitrary code here. You really shouldn't anyway. Just declare your `AttributeKey<T>` variables.

In the define macro, we specify `rdl2::Geometry`. This indicates that, in addition to the attributes we're defining here, we expect
to have all the attributes that `rdl2::Geometry` and its parent classes define as well.

In the define section, you are in a function scope, with a local variable named _sceneClass_, which is the SceneClass being defined.
You should call the `declareAttribute<T>()` method
(see [`lib/scene/rdl2/SceneClass.h`](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/SceneClass.h) for
 documentation) for each attribute and assign it to its corresponding `AttributeKey<T>` that you declared.

#### vector types
Since you're in a function scope, you can also write short snippets of code that that make things more convenient. For example, to
provide a default value for a FloatVector attribute, this is perfectly acceptable:

```cpp
// attributes.cc
RDL2_DSO_ATTR_DEFINE(rdl2::Geometry)
  
    rdl2::FloatVector myFloats;
    myFloats.push_back(1.23f);
    myFloats.push_back(4.56f);
    attrMyFloats =
        sceneClass.declareAttribute<rdl2::FloatVector>("my floats", myFloats);
  
RDL2_DSO_ATTR_END
```

#### enum types
RDL2 does not have any native enum type. Instead, we represent enums as an rdl2::Int. However, since the `attributes.cc` file can't
include any outside dependencies, these can be somewhat opaque. As a convention, we recommend that enum attributes add metadata
which links the integer value (metadata key) to a user-friendly string (metadata value). This lets content tools and scene
introspection tools display more useful information for both the SceneClass and any SceneObjects stamped out from it.

For example:

```cpp
// attributes.cc
RDL2_DSO_ATTR_DEFINE(rdl2::Map)
  
    attrGamma =
        sceneClass.declareAttribute<rdl2::Int>("gamma", 2);
    sceneClass.setMetadata(attrGamma, "0", "off");
    sceneClass.setMetadata(attrGamma, "1", "on");
    sceneClass.setMetadata(attrGamma, "2", "auto");
  
RDL2_DSO_ATTR_END
```

### The \<ClassName\>.json file
For plug-in types that use JSON to declare their attributes, the `attributes.cc` file will be generated
automatically at build time.

Here's an example of a JSON file for a Map shader that defines several attributes of differing types:

_RampMap.json_
```json
{
    "name": "RampMap",
    "type": "Map",
    "attributes": {
        "attrPositions": {
            "name": "positions",
            "type": "FloatVector",
            "default": "{0.0, 0.25, 0.75, 1.0}",
            "comment": "Color ramp",
            "group": "Ramp Knot"
        },
        "attrColors": {
            "name": "colors",
            "type": "RgbVector",
            "default": "{Rgb(0.0), Rgb(0.25), Rgb(0.75), Rgb(1.0)}",
            "comment": "List of colors on the ramp",
            "group": "Ramp Knot"
        },
        "attrRampType": {
            "name": "ramp_type",
            "label": "ramp type",
            "type": "Int",
            "default": "0",
            "flags": "FLAGS_ENUMERABLE",
            "enum": {
                "v": "0",
                "u": "1",
                "diagonal": "2",
                "radial": "3",
                "circular": "4",
                "box": "5",
                "uxv": "6",
                "four corner": "7",
                "input": "8"
            },
            "group": "Ramp properties"
        },
        "attrSpace": {
            "name": "space",
            "type": "Int",
            "default": "0",
            "flags": "FLAGS_ENUMERABLE",
            "enum": {
                "render": "0",
                "camera": "1",
                "world": "2",
                "screen": "3",
                "object": "4",
                "reference": "5",
                "texture": "6"
            },
            "group": "Ramp properties"
        },
        "attrCamera": {
            "name": "camera",
            "type": "SceneObject*",
            "flags": "FLAGS_NONE",
            "interface": "INTERFACE_CAMERA",
            "comment": "Camera used to define camera and screen space",
            "group": "Ramp properties"
        }
    }
}
```

Refer to the [SceneClass](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/SceneClass.h)
source code, the [scene_rdl2]({{ "/developer-reference/scene_rdl2-library/" | absolute_url }}) page, or the existing plug-ins
for more examples of how to declare SceneClass attributes and their metadata.

----
## The Plug-in's Class Definition
This is where you flesh out the actual C++ class that extends the parent RDL2 type. A bare bones `MyTeapotGeometry.cc`
file might look like this:

```cpp
// MyTeapotGeometry.cc
#include <scene/rdl2/rdl2.h>
  
#include "attributes.cc"
  
using namespace arras;
  
RDL2_DSO_CLASS_BEGIN(MyTeapotGeometry, rdl2::Geometry)
  
public:
    RDL2_DSO_DEFAULT_CTOR(MyTeapotGeometry)
  
RDL2_DSO_CLASS_END(MyTeapotGeometry)
```

You may include other third party libraries in the `MyTeapotGeometry.cc` file. Notice that we explicitly include
`attributes.cc`, to bring in the attribute variables in the anonymous namespace.

The class begin and end macros establish a class scope. Each macro requires the name of the class, which is
`MyTeapotGeometry` in this case. Additionally, the begin macro requires the name of the parent class you're extending,
which is `rdl2::Geometry` in this case.

Many DSOs don't have anything to do in the constructor. If this is the case, you can use the default ctor macro to
stamp out a default constructor. This is not a C++ "default" constructor that takes no arguments. It's a constructor
that takes 2 arguments, but does nothing but pass them along to the parent class constructor.

If you do have something to do in the constructor, it must have a specific signature. For example:

```cpp
// MyTeapotGeometry.cc
RDL2_DSO_CLASS_BEGIN(MyTeapotGeometry, rdl2::Geometry)
  
public:
    MyTeapotGeometry(const rdl2::SceneClass& sceneClass, const std::string& name);
  
private:
    int mMyPrivateVariable;
  
RDL2_DSO_CLASS_END(MyTeapotGeometry)
  
MyTeapotGeometry::MyTeapotGeometry(const rdl2::SceneClass& sceneClass, const std::string& name) :
    Parent(sceneClass, name),
    mMyPrivateVariable(42)
{
    // Do initialization-y things, but for private variables only.
    // Your attribute values, accessible via get(attrMyAttribute),
    // HAVE NOT been set yet (use the virtual update() function to
    // initialize based on attribute values).
}
```

At this point, you can declare and define any functions you'd like, including virtual functions that you must
override for your custom type to be complete. For example, since our teapot extends `rdl2::Geometry` we must
override the `createProcedural()` method, which is pure virtual.

```cpp
// MyTeapotGeometry.cc
RDL2_DSO_CLASS_BEGIN(MyTeapotGeometry, rdl2::Geometry)
  
public:
    RDL2_DSO_DEFAULT_CTOR(MyTeapotGeometry);
    geom::Procedural* createProcedural() const override;
  
RDL2_DSO_CLASS_END(MyTeapotGeometry)
  
geom::Procedural*
MyTeapotGeometry::createProcedural() const
{
    // Call into the geometry library to get a geom::Procedural...
    return magicTeapotProceduralGenerator();
}
```

----
## The SceneObject::update() Function
In RDL2, attribute values can be updated between renders. (They cannot change during a render -- you get to
keep your sanity.) If you have any data that is built from, or dependent upon, the values of your attributes,
you can react to those changes by overriding the virtual `update()` method. This method is available to all
SceneObjects.

```cpp
// MyTeapotGeometry.cc
RDL2_DSO_CLASS_BEGIN(MyTeapotGeometry, rdl2::Geometry)
  
public:
    RDL2_DSO_DEFAULT_CTOR(MyTeapotGeometry);
    void update() override;
  
RDL2_DSO_CLASS_END(MyTeapotGeometry)
  
void
MyTeapotGeometry::update() const
{
    if (hasChanged(attrShowLid) && get(attrShowLid)) {
        // Show lid change from off to on.
    }
  
    if (hasBindingChanged(attrSpoutRadius)) {
        // Spout radius attribute has had its binding changed.
        // Check the base value with just hasChanged().
    }
}
```

You cannot assume your attributes have been set until you receive the first call to `update()`. Multiple attributes
may have changed for a single call to `update()`, so use the `hasChanged()` and `hasBindingChanged()` functions to
determine how to react. Lastly, you cannot assume that bound objects have had their attributes set or updated
just because the binding changed. (This applies to attributes of type `SceneObject*` as well. You can't assume
the other object has valid attributes yet.)

In fact, RDL2 should be allowed to call `update()` on each SceneObject in parallel if it wants to. You can't
assume anything about the world outside of your SceneObject.

----
## The Plug-in Interfaces
Depending on the plug-in type, each plugin class will potentially:
* implement/override the virtual interface members declared by the base class
* implement one or more of the static functions prototyped in [Types.h](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/Types.h)  
and set the associated inherited function pointer members

The table below lists the plug-in types with name of the function(s) that comprise that plug-in type's "interface"
and the languages involved in writing a plug-in of the given type.

Note: This table is for example purposes only - it may be incomplete. Refer to the documentation
or examples for each specific plug-in type for more information.

|Plug-in Type|Functions (incomplete list)|Language(s)|
|------------|-----------------|-----------|
|Camera|`setFocalLength() setFilmApertureWidth() computeProjectionMatrix()`|C++|
|Displacement|`DisplaceFunc DisplaceFuncv`|C++ ISPC|
|DisplayFilter|`getInputData() DisplayFilterFuncv`|C++ ISPC|
|Geometry|`createProcedural() destroyProcedural() deformed() resetDeformed()`|C++|
|Light|`canIlluminate() eval() intersect() sample()`|C++ ISPC|
|LightFilter|`canIlluminate() eval() sample()`|C++ ISPC|
|Map|`SampleFunc SampleFuncv`|C++ ISPC|
|Material|`ShadeFunc Shadefuncv PresenceFunc`|C++ ISPC|
|NormalMap|`SampleFunc SampleFuncv`|C++ ISPC|
|VolumeShader|`albedo() anisotropy()  emission() extinct()`|C++|

For example, `Map` shader plug-ins implement functions based on the `SampleFunc` and `SampleFuncv` prototypes
and are responsible for computing a `Color` result.
```cpp
// SampleFunc
// This is C++ code
static void
sample(const scene_rdl2::rdl2::Map *self,
       moonray::shading::TLState *tls,
       const moonray::shading::State &state,
       scene_rdl2::math::Color *result);
```

```cpp
// SampleFuncv
// This is ISPC code
static Color
sample(const uniform Map * uniform self,
       uniform ShadingTLState * uniform tls,
       const varying State &state);
```
`Material` shader plug-ins implement functions based on the `ShadeFunc` and `ShadeFuncv` protoypes
and are responsible for configuring a `Bsdf` via the `BsdfBuilder` API.
```cpp
// ShadeFunc
// This is C++ code
static void
shade(const scene_rdl2::rdl2::Material *self,
      moonray::shading::TLState *tls,
      const moonray::shading::State &state,
      moonray::shading::BsdfBuilder &bsdfBuilder);
```

```cpp
// ShadeFuncv
// This is ISPC code
static void
shade(const uniform Material * uniform self,
      uniform ShadingTLState * uniform tls,
      const varying State &state,
      varying BsdfBuilder &bsdfBuilder);
```

----
## Building with CMake
MoonRay includes a CMake module called _MoonrayDso_ which defines two functions to facilitate the building of DSOs,
depending on the plug-in type:
_moonray_dso_simple()_ and _moonray_ispc_dso()_.

ZebraMap's _CMakeLists.txt_ file might contain the following:

```cmake
# CMakeLists.txt
moonray_ispc_dso(ZebraMap
    DEPENDENCIES
        Moonray::rendering_shading
        Moonray::shading_ispc
        SceneRdl2::scene_rdl2)
```

Tip: if you are developing a new plug-in within the moonray or moonshine codebase, you'll also need to edit the
_CMakeLists.txt_ file in the plug-in's parent directory and add a line so that your plug-in's _CMakeLists.txt_
file can be discovered by the build system:

```cmake
# parent directory's CMakeLists.txt
add_subdirectory(ZebraMap)
```

----
## Writing New Plug-ins
See the links below for information specific to each plug-in type.

[Writing Camera Plug-ins](cameras)  
[Writing Displacement Plug-ins](displacement)  
[Writing DisplayFilter Plug-ins](display-filters)  
[Writing Geometry Plug-ins](geometry-procedurals)  
[Writing Light Plug-ins](lights)  
[Writing LightFilter Plug-ins](light-filters)  
[Writing Map Plug-ins](maps)  
[Writing Material Plug-ins](materials)  
[Writing NormalMap Plug-ins](normal-maps)  
[Writing Volume Shader Plug-ins](volume-shaders)
