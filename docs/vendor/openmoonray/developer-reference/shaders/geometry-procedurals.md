---
title: Writing Geometry Procedurals
---
# Writing Geometry Procedurals
Geometry procedurals typically read data from their
parameters and use it to create one of the supported moonray primitives.
The [geometry]({{ "/user-reference/scene-objects/geometry" | absolute_url }}) procedurals included
with Moonray generate primitives in various ways based on their parameters.   Some convert
explicit data from their parameter lists such as `RdlMeshGeometry`.   Others, such as
`SphereGeometry` use their parameters implicitly.  Unlike map shaders geometry procedurals
cannot be chained together.  However, they can reference other scene objects which 
`RdlInstancerGeometry` demonstrates.

Each geometry procedural implements the `generate` method from the inherited 
[Procedural](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/geom/Procedural.h)
 class.
The types of primitives that can be generated are enumerated in
[Api.h](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/geom/Api.h).
Primitives are created by calling one of the helper functions such
as `createPolygonMesh`.  In addition to any geometric data, the helper functions are all passed
a `PrimitiveAttributeTable` and a `LayerAssignmentId`.   The `PrimitiveAttributeTable` is a lookup
table that can be used to attach arbitrary primitive attributes (per face id, per vertex uv...etc) 
to the geometry.   The `LayerAssignmentId` marks a unique combination of
geometry/partName/material/lightSet in layer.
The created primitive can then be added to the scene by calling the
`addPrimitive` method of the
[ProceduralLeaf](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/geom/ProceduralLeaf.h)
class which all geometry procedurals derive from.  In addition to the primitive, this function is
also passed a set of 
[MotionBlurParams](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/geom/MotionBlurParams.h)
 as well as the `parent2render` matrix set which transforms the primitive from object space to render
 including the procedurals `node_xform` transform.

There are typically 3 files that make up a geometry procedural's source:
* _\<ClassName\>.cc_
* [attributes.cc]({{ "/developer-reference/shaders/#defining-the-plug-ins-attributes" | absolute_url }}) 
* CMakeLists.txt


The _.cc_ file is written in C++ and typically contains two class definitions.   The first derives from
`scene_rdl2::rdl2::Geometry` and should be named the same as the plugin.   This class is more of a 
wrapper and contains one important method `createProcedural()` which returns an instance of the
second class that needs to be implemented which should derive from `ProceduralLeaf`.  It is in the
inherited `generate` function that most of the work typically happens.

Here's a bare-bones `generate` function that creates a single point with a settable radius.

```c++
using namespace scene_rdl2::rdl2;
using namespace shading;

void
SimpleProcedural::generate(const GenerateContext &generateContext,
                           const XformSamples &parent2render)
{
    const Geometry *rdlGeometry = generateContext.getRdlGeometry();

    const SimpleGeometry *rdlPointGeometry =
        static_cast<const SimpleGeometry*>(rdlGeometry);

    // vertices
    const size_t vertCount  = 1;
    const size_t motionSampleCount = 1;
    Points::VertexBuffer vertices(vertCount, motionSampleCount);
    vertices(0, 0) = Vec3f(0.f, 0.f, 0.f);

    // radius buffer
    float radius = rdlPointGeometry->get(attrRadius);
    Points::RadiusBuffer radii(vertCount);
    radii.assign(vertCount, radius);

    // layer assignments
    const Layer *rdlLayer = generateContext.getRdlLayer();
    const int defaultAssignmentId =
        rdlLayer->getAssignmentId(rdlPointGeometry,
                                  ""); // default part name
    LayerAssignmentId layerAssignmentId(defaultAssignmentId);

    // add a constant color "Cd" to the primitive attribue table
    PrimitiveAttributeTable pat;
    std::vector<RgbVector> samples = { { Rgb(1.f, 0.f, 0.f) } };
    pat.addAttribute(TypedAttributeKey<Rgb>("Cd"),
                     AttributeRate::RATE_CONSTANT,
                     std::move(samples));

    std::unique_ptr<Points> primitive = createPoints(std::move(vertices),
                                                     std::move(radii),
                                                     std::move(layerAssignmentId),
                                                     std::move(pat));

    if (primitive) {
        addPrimitive(std::move(primitive),
                     generateContext.getMotionBlurParams(),
                     parent2render);
    }
}
```
