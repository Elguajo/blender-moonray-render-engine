---
title: Writing Material Shaders
---
# Writing Material Shaders
### Overview
Many of the topics covered in the general [Writing Shaders]({{ "/developer-reference/shaders/" | absolute_url }}) page apply to Material shaders, and it is advised that you look there first.

MoonRay provides the BsdfBuilder API for writing new Material shaders.  The goal of this API is to provide a relatively simple abstraction for implementing an energy-conserving MoonRay
material without requiring direct low-level access to MoonRays internal constructs, whose construction and configuration can become quite complicated as the Material's complexity grows.

Examples of these internal low-level constructs include the Bsdf class, the BsdfLobe classes, and Fresnel classes. A fully configured BSDF for a complex Material may include dozens of such
constructs, each allocated in a memory arena and carefully weighted and wrapped together to ensure energy conservation. The BsdfBuilder API provides high-level constructs that describe
each of MoonRay's supported shading models, and handles their construction, weighting, Fresnel behavior and energy conservation.

Each of MoonRay's supported shading models is exposed in the form of a `BsdfComponent`. These components are added in an ordered fashion using the BsdfBuilder, which keeps track of
previously added components and provides automatic weighting and Fresnel behavior tracking.

At the time of this writing MoonRay supports the following shading models:

```
MirrorBRDF                           LambertianBRDF              HairRBRDF
MirrorBTDF                           LambertianBTDF              HairTRTBRDF
MirrorBSDF                           FlatDiffuseBRDF             HairTTBTDF
MicrofacetAnisotropicClearcoat       OrenNayarBRDF               HairTRRTBRDF
MicrofacetIsotropicClearcoat         DipoleDiffusion             GlitterFlakeBRDF
MirrorClearcoat                      NormalizedDiffusion         StochasticFlakesBRDF
MicrofacetAnisotropicBRDF            RandomWalkSubsurface        ToonBRDF
MicrofacetIsotropicBRDF              FabricBRDF                  ToonSpecularBRDF
MicrofacetAnisotropicBTDF            VelvetBRDF                  HairToonSpecularBRDF
MicrofacetIsotropicBTDF              EyeCausticBRDF
MicrofacetAnisotropicBSDF            HairDiffuseBSDF             
MicrofacetIsotropicBSDF              HairBSDF
```

The BsdfBuilder API and associated components are implemented in both scalar and vector flavors.

### Source files
There are typically 4 files that make up a Material shader's source:
* _\<ClassName\>.cc_
* _\<ClassName\>.ispc_
* _\<ClassName\>.json_
* CMakeLists.txt

The _.cc_ file is written in C++ and contains the class definition, the constructor/destructor, the `update()` function, and the static scalar `ShadeFunc` function implementation.

The _.ispc_ file is written in ISPC and contains the vector `ShadeFuncv` function implementation.  It is also common for the _.ispc_ source to contain any data structures or enumerations needed by the shader.

Attributes are declared in the _.json_ file via JSON.

### The shade() function
Each Material shader implements two static functions to support MoonRay's scalar and vector execution modes.  The `ShadeFunc` and `ShadeFuncv` function prototypes are defined in scene_rdl2's
[Types.h](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/Types.h).
                                                                                                
Material shaders inherit two protected function pointer members (`mShadeFunc` and `mShadeFuncv`) which they must set, typically in the constructor, to point to the two implementations which are named
`shade()` by convention.

The `shade()` function is responsible for configuring the BSDF using the BsdfBuilder API.

### The moonray::shading::State
The shading [State](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/shading/State.h) provides the shade function with geometric data at the shading point.

### Related ISPC macros
The vectorized shade function (ShadeFuncv) implementation is routinely followed by a call to the `DEFINE_MATERIAL_SHADER` macro which is defined in [ShaderMacros.isph](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/shading/ispc/ShaderMacros.isph)

```
DEFINE_MATERIAL_SHADER(<shader_name>, <shade_function_name>)
```

This macro provides enables profiling of the vectorized shade function and defines a function `ispc::<shader_name>_getSampleFunc()` which is used to get a function pointer to the ispc shade function
from c++ code.

### Examples
Here is a bare-bones simple solid dielectric material example:

#### _SimpleDielectricMaterial.cc_
```c++
#include <rendering/shading/MaterialApi.h>

#include "attributes.cc"
#include "SimpleDielectricMaterial_ispc_stubs.h"
#include "labels.h"

#include <string>

using namespace scene_rdl2;
using namespace moonray::shading;

//---------------------------------------------------------------------------
RDL2_DSO_CLASS_BEGIN(SimpleDielectricMaterial, rdl2::Material)

public:
    SimpleDielectricMaterial(const rdl2::SceneClass& sceneClass, const std::string& name);
    ~SimpleDielectricMaterial() override {}

    virtual void update() override;

private:
    static void shade(const rdl2::Material* mtl,
                      TLState *tls,
                      const State& state,
                      BsdfBuilder& bsdfBuilder);

RDL2_DSO_CLASS_END(SimpleDielectricMaterial)
//---------------------------------------------------------------------------


SimpleDielectricMaterial::SimpleDielectricMaterial(const rdl2::SceneClass& sceneClass,
                                                   const std::string& name) :
    Parent(sceneClass, name)
{
    // Set the inherited function pointers to our shade function implementations
    mShadeFunc = SimpleDielectricMaterial::shade;
    mShadeFuncv = (rdl2::ShadeFuncv) ispc::SimpleDielectricMaterial_getShadeFunc();
}

// This gets called once before shading, and anytime any of the
// shader's attributes get changed during interactive rendering.
// Do any precomputations/allocations here.
void
SimpleDielectricMaterial::update()
{
    // nothing to do here
}

void
SimpleDielectricMaterial::shade(const rdl2::Material* mtl,
                                TLState *tls,
                                const State& state,
                                BsdfBuilder& bsdfBuilder)
{
    // ---------------------------------------------
    // a simple dielectric specular/diffuse material
    // ---------------------------------------------

    // specular BRDF
    const MicrofacetIsotropicBRDF spec(
            state.getN(),
            mtl->get(attrRefractiveIndex),
            evalFloat(mtl, attrRoughness, tls, state),
            ispc::MICROFACET_DISTRIBUTION_GGX,
            ispc::MICROFACET_GEOMETRIC_SMITH);

    // diffuse BRDF
    const LambertianBRDF diffuse(
            state.getN(),
            evalColor(mtl, attrAlbedo, tls, state));


    // The order in which components are added determines how energy
    // is distributed amongst the lobes.

    bsdfBuilder.addMicrofacetIsotropicBRDF(
            spec,
            1.0f,                           // weight
            ispc::BSDFBUILDER_PHYSICAL,     // use physical behavior
            aovSpecular);                   // label for LPE aovs

    bsdfBuilder.addLambertianBRDF(
            diffuse,
            1.0f,                           // weight
            ispc::BSDFBUILDER_PHYSICAL,     // use physical behavior
            aovDiffuse);                    // label for LPE aovs
}
```

#### _SimpleDielectricMaterial.ispc_
```c++
#include <rendering/shading/ispc/MaterialApi.isph>

#include "attributes.isph"
#include "labels.isph"

static void
shade(const uniform Material *      uniform  mtl,
            uniform ShadingTLState *uniform  tls,
      const varying State                    &state,
            varying BsdfBuilder              &bsdfBuilder)
{
    // ---------------------------------------------
    // a simple dielectric specular/diffuse material
    // ---------------------------------------------

    // specular BRDF
    MicrofacetIsotropicBRDF spec;
    MicrofacetIsotropicBRDF_init(
            spec,
            getN(state),
            getAttrRefractiveIndex(mtl),
            evalAttrRoughness(mtl, tls, state),
            MICROFACET_DISTRIBUTION_GGX,
            MICROFACET_GEOMETRIC_SMITH);

    // diffuse BRDF
    LambertianBRDF diffuse;
    LambertianBRDF_init(
            diffuse,
            getN(state),
            evalAttrAlbedo(mtl, tls, state));


    // The order in which components are added determines how energy
    // is distributed amongst the lobes.

    BsdfBuilder_addMicrofacetIsotropicBRDF(
            bsdfBuilder,
            spec,
            1.0f,                           // weight
            BSDFBUILDER_PHYSICAL,           // use physical behavior
            aovSpecular);                   // label for LPE aovs

    BsdfBuilder_addLambertianBRDF(
            bsdfBuilder,
            diffuse,
            1.0f,                           // weight
            BSDFBUILDER_PHYSICAL,           // use physical behavior
            aovDiffuse);                    // label for LPE aovs
}

DEFINE_MATERIAL_SHADER(SimpleDielectricMaterial, shade)
```

#### _SimpleDielectricMaterial.json_
```c++

{
    "name": "SimpleDielectricMaterial",
    "type": "Material",
    "attributes": {
        "attrAlbedo": {
            "name": "albedo",
            "type": "Rgb",
            "default": "Rgb(0.18, 0.18, 0.18)",
            "flags": "FLAGS_BINDABLE",
            "comment" : "the diffuse reflectance"
        },
        "attrRoughness": {
            "name": "roughness",
            "type": "Float",
            "default": "0.3f",
            "flags": "FLAGS_BINDABLE"
        },
        "attrRefractiveIndex": {
            "name": "refractive_index",
            "label": "refractive index",
            "type": "Float",
            "default": "1.5f",
            "comment": "the refractive index, typically between 1.3 and 1.7"
        }
    },
    "labels": {
        "aovDiffuse": "diffuse",
        "aovSpecular": "specular"
    }
}
```
