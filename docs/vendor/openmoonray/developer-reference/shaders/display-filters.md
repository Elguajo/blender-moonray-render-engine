---
title: Writing Display Filters
---
# Writing Display Filters
This page covers how to author a new Display Filter using our plugin API. MoonRay currently contains 18 [display filters]({{ "/user-reference/scene-objects/display-filters/" | absolute_url }}), which themselves can be chained together to achieve new effects. You can find the code for our existing display filter plugins in the [moonshine](https://github.com/OpenMoonRay/moonshine/tree/main/dso) repository. For the DisplayFilter base class, look [here](https://github.com/OpenMoonRay/scene_rdl2/blob/main/lib/scene/rdl2/DisplayFilter.cc).

## Overview
Each Display Filter plugin requires you to author three files:
- **DisplayFilterName.cc**
- **DisplayFilterName.ispc**
- **DisplayFilterName.json**

Unlike with other plugins, where you must author a .cc file for scalar mode and a .ispc file for vector mode, Display Filters require *both* regardless of the mode. DisplayFilter filtering operations always occur in ISPC, while the C++ code acts as the intermediary between the [DisplayFilterDriver](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/rndr/DisplayFilterDriver.cc) and the ISPC code. 

## Mix & Mask
By default, all display filters offer the following attributes:
- `mask`
- `invert_mask`
- `mix`

You are responsible for initializing and updating the corresponding `mMask`, `mInvertMask`, and `mMix` attributes, as well as defining how they operate on your new display filter. We typically assume that the `mask` attribute masks the output to reveal input1, while the `mix` attribute mixes between input1 and the output. We provide an ISPC function called `DISPLAYFILTER_mixAndMask` (see [code](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/displayfilter/DisplayFilter.ispc)) which takes your mix and mask attributes and outputs a float you can use to lerp between input1 and the result. 

## DisplayFilterName.cc

The **DisplayFilterName.cc** file is responsible for processing data and passing it to our ISPC DisplayFilter class to perform the filtering computations. The class declaration will always have these bare bones:

```cpp
// start the DisplayFilter class definition
RDL2_DSO_CLASS_BEGIN(DisplayFilterName, DisplayFilter)

public:
    // constructor, where you must set the corresponding mIspc attributes
    DisplayFilterName(const SceneClass& sceneClass, const std::string& name);

    // get the user attributes and update the mIspc member variables
    virtual void update() override;

private:
    // process the data inputs (including the mask) and update the inputData
    virtual void getInputData(const displayfilter::InitializeData& initData,
                              displayfilter::InputData& inputData) const override;

    // ISPC DisplayFilter
    ispc::DisplayFilterName mIspc;

// end the DisplayFilter class definition
RDL2_DSO_CLASS_END(DisplayFilterName)
```

Two notes on this:
- At the beginning of the constructor for our existing display filters, you will see: 
```cpp 
mFilterFuncv = (DisplayFilterFuncv) ispc::DisplayFilterClassName_getFilterFunc()
``` 
This is the filter function you will export from ISPC. The `DisplayFilterDriver` will call this function when processing all of the display filters. 

- `getInputData()` takes two arguments: *`InitializeData`* and *`InputData`*. `InitializeData` is a struct that contains *`mImageWidth`* and *`mImageHeight`* (padded width and height). The purpose of this function is to fill in [InputData](https://github.com/OpenMoonRay/moonray/blob/main/lib/rendering/displayfilter/DisplayFilter.h), which looks like the following:
```cpp
struct InputData 
{
    // vector of inputs (should include any masks as well)
    SceneObjectVector mInputs;
    // window width required for each input, in the same order as the inputs
    vector<int> mWindowWidths;
}
```

## DisplayFilterName.ispc
The **DisplayFilterName.ispc** file is responsible for performing filtering on the provided input(s). A barebones ispc file would look like this:

```cpp
struct DisplayFilterName
{
    bool mMask;         // was a mask provided in the inputs?
    bool mInvertMask;   // should we invert the provided mask?
    float mMix;         // mix amount between input1 and output
    
    // insert any other attributes here
}

// define function that will get const pointer to display filter subclass
export const uniform DisplayFilterName * uniform
DisplayFilterName_get(const uniform DisplayFilter * uniform displayFilter)
{
    return DISPLAYFILTER_GET_ISPC_CPTR(DisplayFilterName, displayFilter);
}

static void
filter(const uniform DisplayFilter * uniform me,
       const uniform InputBuffer * const uniform * const uniform inputBuffers,
       const varying DisplayFilterState * const uniform state,
       varying Color * uniform result)
{
    // get pointer to display filter subclass
    const uniform DisplayFilterName * uniform self = DisplayFilterName_get(me);
    // get first input from our input buffers vector
    const uniform InputBuffer const * uniform inBuffer = inputBuffers[0];
    // get pixel from the input buffer
    varying Color src = InputBuffer_getPixel(inBuffer, state->mOutputPixelX, state->mOutputPixelY);

    // do filtering computations here

    // get the mix amount
    float mix = DISPLAYFILTER_mixAndMask(self->mMix,
                                         self->mMask ? inputBuffers[1] : nullptr,
                                         state->mOutputPixelX,
                                         state->mOutputPixelY,
                                         self->mInvertMask);
    // if mix is zero, return the first input
    if (isZero(mix)) {
        *result = src;
        return;
    }

    // if mix is one, return result as is; otherwise, lerp between input1 and output
    if (!isOne(mix)) {
        *result = lerp(src, *result, mix);
    }
}

// export our filter func as DisplayFilterName_getFilterFunc() for use in our cpp 
// DisplayFilterDriver, which processes all of our display filters
DEFINE_DISPLAY_FILTER(DisplayFilterName, filter)
```

Fill out the filter function to perform whatever filtering you wish. Keep in mind to also do the mixing and masking before outputting the result. 

## DisplayFilterName.json
This is simply where all of your attributes are defined. No need to define `mask`, `invertMask`, or `mix`, as these are default attributes that all display filters have in common. 
