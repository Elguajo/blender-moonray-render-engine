---
title: MoonRay Source Structure
---
# MoonRay Source Structure

***openmoonray*** is the top-level repository for MoonRay open source. The actual source code is contained in a number of other repositories referenced as git submodules.

## Arras

At the top-level, ***arras*** contains repositories relating to the Arras execution and process communication system. Most of the code under *arras* is independent of MoonRay, and can be built and used separately if desired. 

- ***arras/arras4_core*** links to a repository containing the C++ libraries implementing Arras. The libraries are required by the example application arras_render, and by the MoonRay Hydra plugin HdMoonray.

- ***arras/arras_render*** is a Qt5 application that provides an example of MoonRay integration using Arras. It needs the MoonRay libraries to build and run.

- ***arras/distributed*** contains additional code needed to use Arras in distributed mode. ***arras4_node*** is a C++ service that runs on every render machine, ***minicoord*** is a Python service that manages a pool of render machines.

## MoonRay

The top-level ***moonray*** directory contains the repositories that implement MoonRay and its associated plugins. Most of the code under *moonray* doesn't require Arras to build, but it is needed by the *moonray_arras* libraries and by the Hydra plugin *HdMoonRay*.

- ***moonray/scene_rdl2*** is the repository that provides MoonRay's scene representation and a number of utility libraries.

- ***moonray/moonray*** is the repository that implements the MoonRay render engine and the moonray command-line renderer. The code is divided into roughly 20 libraries. *moonray* also contains a set of basic scene object (shader) plugins.

- ***moonray/moonray_dcc_plugins*** plugins for using moonray nodes in third-party DCC tools

- ***moonray/moonray_gui*** implements the moonray_gui Qt application, that can be used to view render progress and final results.

- ***moonray/render_profile_viewer*** a Python tool for comparing render logs

- ***moonray/moonshine*** contains a far more extensive set of scene object plugins.

- ***moonray/moonshine_usd*** has the Usd and UsdInstance scene objects.

- ***moonray/moonray_arras*** contains the client and server components needed to use MoonRay with Arras.

- ***moonray/hydra*** has the Hydra plugin for MoonRay, HdMoonRay.

- ***moonray/mcrt_denoise*** has the denoiser code.






