---
title: Writing Volume Shaders
---
# Writing Volume Shaders

## Introduction
Volume shaders derive from the
[VolumeShader](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl/VolumeShader.h)
 interface class and allow the customization of various volume properties.  They are required to
 implement the following methods:
 *extinct*, *albedo*, *emission*, *anisotropy*, *hasExtinctionMapBinding*, and *updateBakeRequired*.
In addition to these required methods, volume shaders should also set the `VolumeShader::Properties`
bitmask in their *update* method and return it from their *getProperties* method.

There are typically 3 files that make up a volume shaders's source:
* _\<ClassName\>.cc_
* [attributes.cc]({{ "/developer-reference/shaders/#defining-the-plug-ins-attributes" | absolute_url }}) 
* CMakeLists.txt

## Parameters
Volume shaders define parameters in the *attribute.cc* file.  In addition to the user defined
 parameters, all volume shaders inherit several parameters: *bake_resolution_mode*, *bake_division*,
 *bake_voxel_size*, and *surface_opacity_threshold*.   Moonray bakes any bound maps into a voxel
 grid based on the *bake* parameters.   The *surface_opacity_threshold* sets the opacity that's
 considered the 'surface' for computing position.

## Properties
The *update* method should set a `VolumeShader::Properties` bitmask which informs Moonray
of the nature of the volume.  The following properties are settable:
* `IS_EXTINCTIVE` - Set this if the *extinct* method outputs a color value other than black
* `HOMOGENOUS_EXTINC` - Set this if there are no map bindings that modify the output of the *extinct* method
* `IS_SCATTERING` - Set this if the *albdeo* method outputs a color value other than black 
* `HOMOGENOUS_ALBEDO` - Set this if there are no map bindings that modify the output of the *albedo* method
* `IS_EMISSIVE` - Set this if the *emission* method outputs a color value other than black 
* `HOMOGENOUS_EMISS` - Set this if there are no map bindings that modify the output of the *emission* method
* `ISOTROPIC_PHASE` - Set this if the *anisotropy* method outputs zero and there are no map bindings that modify it's output

The example below sets the `unsigned mProp` member variable based on the input parameters
and bindings.
```c++
void
VdbVolume::update()
{
    // If map binding does not exist, then property is homogenous.
    mProp = 0x0;
    if (getBinding(attrExtinctionGainMult)) {
        mProp |= IS_EXTINCTIVE;
    } else if (!isBlack(get(attrExtinctionGainMult))) {
        mProp |= IS_EXTINCTIVE | HOMOGENOUS_EXTINC;
    }

    if (getBinding(attrAlbedoMult)) {
        mProp |= IS_SCATTERING;
    } else if (!isBlack(get(attrAlbedoMult))) {
        mProp |= IS_SCATTERING | HOMOGENOUS_ALBEDO;
    }

    if (getBinding(attrIncandGainMult)) {
        mProp |= IS_EMISSIVE;
    } else if (!isBlack(get(attrIncandGainMult))) {
        mProp |= IS_EMISSIVE | HOMOGENOUS_EMISS;
    }

    if (get(attrAnisotropy) == 0.0f && getBinding(attrAnisotropy) == nullptr) {
        mProp |= ISOTROPIC_PHASE;
    }
}
```

In addition to setting the bitmask in *update*, the shader should return it from the
overriden *getProperties* method as in the example below.
```c++
virtual finline unsigned getProperties() const override
{
    return mProp;
}
```

## Required Methods

### extinct
The *extinct* method allows the modification of the volume's density.  The input density and 
the shading state are provided.   The output extinction should be limited to positive values.
The example below multiplies the input density with a bindable user defined parameter and 
clamps the output at zero.

```c++
virtual scene_rdl2::math::Color extinct(moonray::shading::TLState *tls,
                                        const moonray::shading::State &state,
                                        const scene_rdl2::math::Color& density) const override
{
    scene_rdl2::math::Color result = density * evalColor(this, attrExtinctionGainMult, tls, state);
    // Map shader can produce negative values. An extinction value cannot be negative.
    result = scene_rdl2::math::max(result, scene_rdl2::math::sBlack);
    return result;
}
```

### albedo
The *albedo* method allows the modification of the volume's color.  The input density and 
the shading state are provided.   The output color should be limited to positive values.
The example below multiplies the input density with a bindable user defined parameter and 
clamps the output at zero.

```c++
virtual scene_rdl2::math::Color albedo(moonray::shading::TLState *tls,
                           const moonray::shading::State &state,
                           const scene_rdl2::math::Color& density) const override
{
    scene_rdl2::math::Color result = density * evalColor(this, attrAlbedoMult, tls, state);
    // Map shader can produce negative values. An albedo value cannot be negative.
    result = scene_rdl2::math::max(result, scene_rdl2::math::sBlack);
    return result;
}
```

### emission
The *emission* method allows the modification of the volume's emission.  The input density and 
the shading state are provided.   The output color should be limited to positive values.
The example below multiplies the input density with a bindable user defined parameter and 
clamps the output at zero.

```c++
virtual scene_rdl2::math::Color emission(moonray::shading::TLState *tls,
                             const moonray::shading::State &state,
                             const scene_rdl2::math::Color& density) const override
{
    scene_rdl2::math::Color result = density * evalColor(this, attrIncandGainMult, tls, state);
    // Map shader can produce negative values. An emission value cannot be negative.
    result = scene_rdl2::math::max(result, scene_rdl2::math::sBlack);
    return result;
}
```

### anisotropy
The *anisotropy* method allows the modification of the volume's anisotropy or how forward
or backward scattering the volue is.  The input state is provided.  The output color should
be clamped from -1 to 1.
The example below evaluates the bindable anistropy parameter and clamps the result.

```c++
virtual float anisotropy(moonray::shading::TLState *tls,
                         const moonray::shading::State &state) const override
{
    return scene_rdl2::math::clamp(evalFloat(this, attrAnisotropy, tls, state),
                                   -1.0f, 1.0f);
}
```

### hasExtinctionMapBinding
The *hasExtinctionMapBinding* method should return true or false based on whether or not
the output of the *extinction* method uses any map bindings.
The example below checks if there the parameter is bound.

```c++
virtual bool hasExtinctionMapBinding() const override
{
    return getBinding(attrExtinctionGainMult) != nullptr;
}
```

### updateBakeRequired
As noted above, Moonray bakes any bound maps into voxel grids using the inherited 
*bake* parameters.  This method should return true or false based on whether or not any
of these parameter or any map bindings have changed as shown in the example below.
```c++
    virtual bool updateBakeRequired() const override
    {
        bool updateMapBinding = false;
        if (hasExtinctionMapBinding()) {
            updateMapBinding |= getBinding(attrExtinctionGainMult)->updateRequired();
        }
        return updateMapBinding ||
               hasChanged(scene_rdl2::rdl2::VolumeShader::sBakeResolutionMode) ||
               hasChanged(scene_rdl2::rdl2::VolumeShader::sBakeDivisions) ||
               hasChanged(scene_rdl2::rdl2::VolumeShader::sBakeVoxelSize) ||
               hasBindingChanged(attrExtinctionGainMult) ||
               // If any map bindings are added or removed, we must rebake the volume shader
               // in case velocity is being applied. We don't know if velocity is applied until
               // we bake the volume shader, so this is a precaution.
               hasBindingChanged(attrAlbedoMult) ||
               hasBindingChanged(attrIncandGainMult) ||
               hasBindingChanged(attrAnisotropy);
    }
```

