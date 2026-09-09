---
title: Writing Light Shaders
---
# Writing Light Shaders
This page covers how to write new types of Lights for MoonRay. Unlike other categories in the Developer's Guide, there is no formalized API for designing and writing a plugin in one location yet. As such, Lights must currently be added at the MoonRay layer, not the MoonShine layer. Adding a new type of light is still relatively straightforward.

## Overview
Each Light plugin reguires you to:
- Create a default scene object class in `moonray/dso/light` to read and store attributes
- Create a light class in `moonray/lib/rendering/pbr/light` to do the actual work
- Change the factory in `moonray/lib/rendering/pbr/core` to instantiate the light when it finds the scene class

## Creating the Light scene object
Every existing light requires a "default" class in `moonray/dso/light`. Each one is identical, outside of the name. Here's what `SphereLight` looks like:

```c++
#include <scene_rdl2/scene/rdl2/rdl2.h>

#include "attributes.cc"

using namespace scene_rdl2;

RDL2_DSO_CLASS_BEGIN(SphereLight, rdl2::Light)

public:
    RDL2_DSO_DEFAULT_CTOR(SphereLight)

RDL2_DSO_CLASS_END(SphereLight)
```

Differences appear when authoring the light's attributes. Unlike maps or materials where you author a `.json` that is converted into an associated `attributes.cc` at compile time, you must directly author `attributes.cc` here.

A number of common attributes are handled by the parent scene object class, `rdl2::Light`. This includes (but is not limited to) color, intensity, exposure, camera visibility, and shadowing options. 

This file has a simple call to instantiate the common Light attributes, and the attributes authored here afterward are unique to this Light.

Light attribute files are structured like this:

```c++

#include <scene_rdl2/scene/rdl2/rdl2.h>

using namespace scene_rdl2;

RDL2_DSO_ATTR_DECLARE

    // declare all specific attributes here
    rdl2::AttributeKey<rdl2::Float>     attrMyAttribute;
    DECLARE_ATTR_KEYS_CLEAR_RADIUS

// instantiate parent attributes
RDL2_DSO_ATTR_DEFINE(rdl2::Light)

    // define all declared attributes here
    attrMyAttribute = sceneClass.declareAttribute<rdl2::Float>("my_attribute", 1.0f);
    sceneClass.setMetadata(attrMyAttribute, rdl2::SceneClass::sComment,
        "This is the mouseover text a user would read in a DCC for my_attribute");

    DECLARE_ATTRS_CLEAR_RADIUS

    // apply grouping and labels, and add to the scene. creates subfolders in DCC
    sceneClass.setGroup("Properties", attrMyAttribute);
    SET_ATTR_GRP_CLEAR_RADIUS

RDL2_DSO_ATTR_END

```

## Creating the Light Class

The actual work is done in the libraries. Lights are all written in `moonray/lib/rendering/pbr/light`. 

There are typically 3 files that make up a Light's source:
* _\<ClassName\>.cc_
* _\<ClassName\>.h_
* _\<ClassName\>.ispc_

Notice that `.isph` is not necessary-- setup for the ispc struct and members is handled in the header, often using macros found in the shared header `Light.hh`.

`Light.h` is the header that defines both parent classes: `Light` and `LocalParamLight` (which is a `Light`). Any bounded light with locally-defined geometry, such as a sphere or cylinder light, is the latter. 

Lights are instantiated and updated in C++ and the relevant information is passed over to ispc during vectorized rendering.

### Instantiating Attributes in the Light

Every Light requires static keys for looking up each attribute defined in its scene object class.
It is expected to initialize them once when the first Light of this type is instantiated.

In the header:
```c++
class MyLight : public LocalParamLight
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
bool                                                    MyLight::sAttributeKeyInitialized;
scene_rdl2::rdl2::AttributeKey<scene_rdl2::rdl2::Float> MyLight::sMyAttributeKey;

...
void
MyLight::initAttributeKeys(const scene_rdl2::rdl2::SceneClass &sc)
{
    if (sAttributeKeyInitialized) {
        return;
    }

    MOONRAY_START_NON_THREADSAFE_STATIC_WRITE

    sAttributeKeyInitialized = true;

    // The string here MUST match the one defined in the dso
    sMyAttributeKey = sc.getAttributeKey<scene_rdl2::rdl2::Float>("my_attribute");

    ...

    INIT_ATTR_KEYS_CLEAR_RADIUS

    MOONRAY_FINISH_NON_THREADSAFE_STATIC_WRITE
}

```

### Required Functions

The following public functions need to be implemented in a custom Light.

Detailed comments for each can be found in `Light.h`.

```c++
// C++ only.

    // Handle parent attributes, transformations, precalculations
    virtual bool update(const scene_rdl2::math::Mat4d& world2render) override;

    // Flags for the path tracer. Implementations are just return true/false
    virtual bool isBounded() const override;
    virtual bool isDistant() const override;
    virtual bool isEnv() const override;

    virtual scene_rdl2::math::BBox3f getBounds() const override;

    /// From: "Importance Sampling Techniques for Path Tracing in Participating Media"
    /// EGSR2012 Christopher Kulla and Marcos Fajardo
    virtual scene_rdl2::math::Vec3f getEquiAngularPivot(
        const scene_rdl2::math::Vec3f& r, float time) const override;

// C++ and ISPC. These are render-space intersection and sampling functions

    // Check if a light can affect a given position and normal
    virtual bool canIlluminate(const scene_rdl2::math::Vec3f p,
        const scene_rdl2::math::Vec3f *n, float time, float radius,
        const LightFilterList* lightFilterList) const override;

    virtual bool intersect(const scene_rdl2::math::Vec3f &p, 
        const scene_rdl2::math::Vec3f *n, const scene_rdl2::math::Vec3f &wi, float time,
        float maxDistance, LightIntersection &isect) const override;

    // Get a point on the light, see if it can illuminate the given position and normal
    virtual bool sample(const scene_rdl2::math::Vec3f &p,
        const scene_rdl2::math::Vec3f *n, float time, 
        const scene_rdl2::math::Vec3f& r, scene_rdl2::math::Vec3f &wi, 
        LightIntersection &isect, float rayDirFootprint) const override;

    // Get the light's emission in the direction of wi
    virtual scene_rdl2::math::Color eval(mcrt_common::ThreadLocalState* tls,
        const scene_rdl2::math::Vec3f &wi, const scene_rdl2::math::Vec3f &p,
        const LightFilterRandomValues& filterR, float time,
        const LightIntersection &isect, bool fromCamera,
        const LightFilterList *lightFilterList, float rayDirFootprint, 
        float *pdf = nullptr) const override;
```

## Instantiating the Lights in the Renderer

There's a function in `moonray/lib/rendering/pbr/core/Scene.cc` that checks the name of the rdl scene object and matches it with the actual class. Include the header of your custom Light in this file, and modify this function to add your light:

```c++
Light*
Scene::createLightFromRdlLight(const rdl2::Light* rdlLight)
{
    const rdl2::SceneClass &lightClass = rdlLight->getSceneClass();
    const std::string &className = lightClass.getName();
    Light *light = nullptr;
    if (className == "CylinderLight") {
        light = new CylinderLight(rdlLight);
    } else if (className == "MyLight") {
        light = new MyLight(rdlLight);
    //...
    } else {
        MNRY_ASSERT(!"Unknown light type.");
    }
    return light;
}
```
