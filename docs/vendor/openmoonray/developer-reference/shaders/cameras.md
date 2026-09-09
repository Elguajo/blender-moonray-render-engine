---
title: Writing Camera Shaders
---
# Writing Camera Shaders
This page explains how to write new types of Cameras for MoonRay.

## Overview
Each Camera plugin reguires you to:
- Create a default scene object class in `moonray/dso/camera` to read and store attributes
- Create a camera class in `moonray/lib/rendering/pbr/camera` to do the actual work
- Change the factory in `moonray/lib/rendering/pbr/core` to instantiate the camera when it finds the scene class

## Creating the Camera scene object
Every existing camera requires a class in `moonray/dso/camera`. Here's what `SphericalCamera` looks like:

```c++
#include <scene_rdl2/scene/rdl2/rdl2.h>

#include "attributes.cc"

using namespace scene_rdl2;

RDL2_DSO_CLASS_BEGIN(SphericalCamera, rdl2::Camera)

public:
    RDL2_DSO_DEFAULT_CTOR(SphericalCamera)

RDL2_DSO_CLASS_END(SphericalCamera)
```

Differences appear when authoring the cameras's attributes. Unlike maps or materials where you author a `.json` that is converted into an associated `attributes.cc` at compile time, you must directly author `attributes.cc` here.

A number of common attributes are handled by the parent scene object class, `rdl2::Camera`. This includes (but is not limited to) 
near/far clipping planes, shutter open/close times, and an initial medium (e.g. a water material). 

This file has a simple call to instantiate the common Camera attributes, and the attributes authored here afterward are unique to this Camera.

Camera attribute files are structured like this:

```c++

#include <scene_rdl2/scene/rdl2/rdl2.h>

using namespace scene_rdl2;

RDL2_DSO_ATTR_DECLARE

    // declare all specific attributes here
    rdl2::AttributeKey<rdl2::Float>     attrMyAttribute;

// instantiate parent attributes
RDL2_DSO_ATTR_DEFINE(rdl2::Camera)

    // define all declared attributes here
    attrMyAttribute = sceneClass.declareAttribute<rdl2::Float>("my_attribute", 1.0f);
    sceneClass.setMetadata(attrMyAttribute, rdl2::SceneClass::sComment,
        "This is the mouseover text a user would read in a DCC for my_attribute");

    // apply grouping and labels, and add to the scene. creates subfolders in DCC
    sceneClass.setGroup("Properties", attrMyAttribute);

RDL2_DSO_ATTR_END

```

## Creating the Camera Class

The actual work is done in the libraries. Cameras are all written in `moonray/lib/rendering/pbr/camera`. 

There are typically 2 files that make up a Camera's source:
* _\<ClassName\>.cc_
* _\<ClassName\>.h_

`Camera.h` is the header that defines the parent class: `Camera`. 

Cameras are instantiated and updated in C++.  There is no vectorized ispc Camera code.

### Instantiating Attributes in the Camera

Every Camera requires static keys for looking up each attribute defined in its scene object class.
It is expected to initialize them once when the first Camera of this type is instantiated.

In the header:
```c++
class MyCamera : public Camera
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
bool                                                    MyCamera::sAttributeKeyInitialized;
scene_rdl2::rdl2::AttributeKey<scene_rdl2::rdl2::Float> MyCamera::sMyAttributeKey;

...
void
MyCamera::initAttributeKeys(const scene_rdl2::rdl2::SceneClass &sc)
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

The following public functions need to be implemented in a custom Camera.

Detailed comments for each can be found in `Camera.h`.

```c++
    virtual bool getIsDofEnabledImpl() const = 0;
    virtual bool hasFrustumImpl() const { return false; }
    virtual void computeFrustumImpl(mcrt_common::Frustum *frust, float t, bool useRenderRegion) const;
    virtual void bakeUvMapsImpl();
    virtual void getRequiredPrimAttributesImpl(shading::PerGeometryAttributeKeySet &keys) const;
    virtual float computeZDistanceImpl(const scene_rdl2::math::Vec3f &p, const scene_rdl2::math::Vec3f &o,
                                       float time) const;
    virtual void updateImpl(const scene_rdl2::math::Mat4d& world2render) = 0;

    virtual void createRayImpl(mcrt_common::RayDifferential* dstRay,
                           float x,
                           float y,
                           float time,
                           float lensU,
                           float lensV) const = 0;

    virtual StereoView getStereoViewImpl() const { return StereoView::CENTER; }

```

## Instantiating the Camera in the Renderer

There's a function in `moonray/lib/rendering/pbr/core/Scene.cc` that checks the name of the rdl scene object and matches it with the actual class. Include the header of your custom Camera in this file, and modify this function to add your camera:

```
namespace {
std::unique_ptr<Camera> cameraFactory(const rdl2::Camera* rdlCamera)
{
    const rdl2::SceneClass& cameraClass = rdlCamera->getSceneClass();
    const std::string& className = cameraClass.getName();
    if (className == "PerspectiveCamera") {
        return std::unique_ptr<Camera>(new PerspectiveCamera(rdlCamera));
    } else if (className == "OrthographicCamera") {
        return std::unique_ptr<Camera>(new OrthographicCamera(rdlCamera));
    } else if (className == "SphericalCamera") {
        return std::unique_ptr<Camera>(new SphericalCamera(rdlCamera));
    } else if (className == "BakeCamera") {
        return std::unique_ptr<Camera>(new BakeCamera(rdlCamera));
    } else if (className == "MyCamera") {
        return std::unique_ptr<Camera>(new MyCamera(rdlCamera));
    } else {
        MNRY_ASSERT(!"Should not get here");
        throw std::runtime_error("No valid camera type specified");
    }
}
} // namespace
```

