---
title: Writing Light Filters
---
# Writing Light Filters
This page covers how to write new types of light filters for MoonRay. Unlike other categories in the Developer's Guide, there is no formalized API for designing and writing a plugin in one location yet. As such, light filters must currently be added at the MoonRay layer, not the MoonShine layer. Adding a new type of light filter is still relatively straightforward.

## Overview
Each light filter plugin reguires you to:
- Create a default scene object class in `moonray/dso/lightfilter` to read and store attributes
- Create a light filter class in `moonray/lib/rendering/pbr/lightfilter` to do the actual work
- Change the factory in `moonray/lib/rendering/pbr/core` to instantiate the light filter when it finds the scene class

## Creating the Light Filter scene object
Every existing light filter requires a "default" class in `moonray/dso/lightfilter`. Each one is identical, outside of the name. Here's what `DecayLightFilter` looks like:

```c++
#include <scene_rdl2/scene/rdl2/rdl2.h>

#include "attributes.cc"

using namespace scene_rdl2;

RDL2_DSO_CLASS_BEGIN(DecayLightFilter, rdl2::LightFilter)

public:
    RDL2_DSO_DEFAULT_CTOR(DecayLightFilter)

RDL2_DSO_CLASS_END(DecayLightFilter)
```

Differences appear when authoring the light filter's attributes. Unlike maps or materials where you author a `.json` that is converted into an associated `attributes.cc` at compile time, you must directly author `attributes.cc` here.

A single common attribute is handled by the parent scene object class, `rdl2::LightFilter`. This is the on/off toggle for the light filter. 

This file has a simple call to instantiate the common LightFilter attributes, and the attributes authored here afterward are unique to this light filter.

LightFilter attribute files are structured like this:

```c++

#include <scene_rdl2/scene/rdl2/rdl2.h>

using namespace scene_rdl2;

RDL2_DSO_ATTR_DECLARE

    // declare all specific attributes here
    rdl2::AttributeKey<rdl2::Float>     attrMyAttribute;

// instantiate parent attributes
RDL2_DSO_ATTR_DEFINE(rdl2::LightFilter)

    // define all declared attributes here
    attrMyAttribute = sceneClass.declareAttribute<rdl2::Float>("my_attribute", 1.0f);
    sceneClass.setMetadata(attrMyAttribute, rdl2::SceneClass::sComment,
        "This is the mouseover text a user would read in a DCC for my_attribute");

    // apply grouping and labels, and add to the scene. creates subfolders in DCC
    sceneClass.setGroup("Properties", attrMyAttribute);

RDL2_DSO_ATTR_END

```

## Creating the Light Filter Class

The actual work is done in the libraries. Light filters are all written in `moonray/lib/rendering/pbr/lightfilter`. 

There are typically 3 files that make up a light filter's source:
* _\<ClassName\>.cc_
* _\<ClassName\>.h_
* _\<ClassName\>.ispc_

Notice that `.isph` is not necessary-- setup for the ispc struct and members is handled in the header, often using macros found in the shared header `LightFilter.hh`.

`LightFilter.h` is the header that defines the parent class: `LightFilter`.

Light filters are instantiated and updated in C++ and the relevant information is passed over to ispc during vectorized rendering.

### Instantiating Attributes in the Light Filter

Every light filter requires static keys for looking up each attribute defined in its scene object class.
It is expected to initialize them once when the first light filter of this type is instantiated.

In the header:
```c++
class MyLightFilter : public LightFilter
{
...

private:
    void initAttributeKeys(const scene_rdl2::rdl2::SceneClass &sc);
...
    static bool sAttributeKeyInitialized;
    static scene_rdl2::rdl2::AttributeKey<scene_rdl2::rdl2::Float> sMyAttributeKey;
}
```

In the .cc:
```c++
bool                                                    MyLightFilter::sAttributeKeyInitialized;
scene_rdl2::rdl2::AttributeKey<scene_rdl2::rdl2::Float> MyLightFilter::sMyAttributeKey;

...
void
MyLightFilter::initAttributeKeys(const scene_rdl2::rdl2::SceneClass &sc)
{
    if (sAttributeKeyInitialized) {
        return;
    }

    MOONRAY_START_NON_THREADSAFE_STATIC_WRITE

    sAttributeKeyInitialized = true;

    // The string here MUST match the one defined in the dso
    sMyAttributeKey = sc.getAttributeKey<scene_rdl2::rdl2::Float>("my_attribute");

    ...

    MOONRAY_FINISH_NON_THREADSAFE_STATIC_WRITE
}

```

### Required Functions

The following public functions need to be implemented in a custom light filter.

Detailed comments for each can be found in `LightFilter.h`.

```c++
// C++ only.

    // Handle parent attributes, transformations, precalculations
    virtual void update(const LightFilterMap& lightFilters,
                        const scene_rdl2::math::Mat4d& world2render) = 0;

    virtual bool canIlluminate(const CanIlluminateData& data) const = 0;
    virtual scene_rdl2::math::Color eval(const EvalData& data) const = 0;
    virtual bool needsLightXform() const { return false; }
    virtual bool needsSamples() const { return false; }
```

## Instantiating the Light Filters in the Renderer

There's a function in `moonray/lib/rendering/pbr/core/Scene.cc` that creates and updates the light filters in the Scene.  Include the header of your custom light filter in this file, and modify this function to add your light filter:

```c++
void
Scene::updateLightFilters()
{
...
        if (className == "ColorRampLightFilter") { // Construct filter
            lightFilter = new ColorRampLightFilter(rdlLightFilter);
        } else if (className == "CombineLightFilter") {
            lightFilter = new CombineLightFilter(rdlLightFilter);
        } else if (className == "CookieLightFilter") {
            lightFilter = new CookieLightFilter(rdlLightFilter);
        } else if (className == "CookieLightFilter_v2") {
            lightFilter = new CookieLightFilter_v2(rdlLightFilter);
        } else if (className == "BarnDoorLightFilter") {
            lightFilter = new BarnDoorLightFilter(rdlLightFilter);
        } else if (className == "DecayLightFilter") {
            lightFilter = new DecayLightFilter(rdlLightFilter);
        } else if (className == "IntensityLightFilter") {
            lightFilter = new IntensityLightFilter(rdlLightFilter);
        } else if (className == "RodLightFilter") {
            lightFilter = new RodLightFilter(rdlLightFilter);
        } else if (className == "VdbLightFilter") {
            lightFilter = new VdbLightFilter(rdlLightFilter);
        } else if (className == "MyLightFilter") {
            lightFilter = new MyLightFilter(rdlLightFilter);
        } else {
            MNRY_ASSERT(!"Unknown light filter type.");
        }
...
}
```

