---
title: Developer's Guide
---
# Developer's Guide

If you want to develop with the MoonRay code base, the first step is to clone the repository and make sure you can build it:

[Building MoonRay]({{ "/getting-started/installation/building-moonray/" | absolute_url }})

The overall structure of the source repositories is detailed here:

[Source structure](source-structure)

Most development tasks require some knowledge of MoonRay's internal scene description format, **RDL2**. This is provided by the **scene_rdl2** library, described here:

[The scene_rdl2 library](scene_rdl2-library). 

The file formats used to store scenes are described here:

[RDL2 scene formats]({{ "/getting-started/about/rdl-scene-format" | absolute_url }})

If you want to translate scenes to or from RDL2 format, scene_rdl2 may be all you need.

You can extend MoonRay itself by authoring new **shader** plugins. Instructions on how to do this are here:

[Writing new shaders](shaders/index)

**Arras** is used to integrate interactive MoonRay rendering into applications. The following pages have more information:


[Arras Overview](arras/index)  

[Session Definitions](arras/arras-session-definitions)  

[Client API](arras/arras-client-api)

[Running distributed Arras](arras/distributed-arras)

[Coding Standards](coding-standards/index)
