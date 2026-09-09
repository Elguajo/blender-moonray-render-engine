---
title: Arras Client API
---

# Arras Client API

Applications can use the Arras Client API to integrate interactive MoonRay rendering. The client API itself is not specific to MoonRay : MoonRay clients need to use the additional libraries in mcrt_messages and mcrt_dataio for the MoonRay specific parts. The client code does not link directly to the main MoonRay renderer libraries, or to the MoonRay Arras computations in mcrt_computation : these are loaded automatically by the Arras system. 

Generally a client will need to link to the scene_rdl2 library, in order to generate scene descriptions in MoonRay's native RDLB format. The MoonRay computations do not support RDLA format, for performance reasons, although it would not be difficult to add this. The client also needs to be able to load the "proxy" libraries for the scene objects it uses. These proxies contain the attribute descriptions for the objects without the actual rendering code. scene_rdl2 will use the proxies to validate the scene description, and so many possible errors will be detected in the client before transmission to the renderer.

## Example Client

For simplicity, the code defines constants for some values that would usually be set based on user input:

```c++
const std::string COORDINATOR_URL("arras:local");
const std::string SESSION_NAME("single_render");
const unsigned NUM_MACHINES = 1;
const std::string SCENE_FILE("example.rdla");
const std::string SCENE_DELTA_FILE("example_delta.rdla");
```

The client is configured to use Arras local mode, by specifying "arras:local" as the Coordinator URL. To use distributed mode, this should be changed to the URL of a Coordinator service : the rest of the code remains unchanged.

A client normally needs to translate scene data from some other format into MoonRay's native RDLB before sending it to Arras. For this example, we will just load the data from RDLA format files.

The central class in the Arras client API is `SDK`. Each instance of this class represents a single session : to run multiple sessions at the same time, the client would simply create multiple SDK objects. Similarly, an instance of [`ClientReceiverFb`](../doxygen-pages/#mcrt_dataioclientreceiverfb) is used to decode incoming rendered frames from a single session:

```c++
std::unique_ptr<mcrt_dataio::ClientReceiverFb> theFbReceiver;
std::unique_ptr<arras4::sdk::SDK> theSdk;
```

The main() function begins by initializing these objects:

**Setup**
```c++
int main(int argc, char* argv[])
{
        theSdk.reset(new arras4::sdk::SDK);
        theSdk->setSyncSend();
        theSdk->setMessageHandler(&messageHandler);
        theSdk->setStatusHandler(&statusHandler);
        theSdk->setExceptionCallback(&exceptionCallback);
 
        theFbReceiver.reset(new mcrt_dataio::ClientReceiverFb);
    ...
```

`setSyncSend()` causes the `SDK` `sendMessage` function to block until the message has been sent. Using `setAsyncSend()` instead would make `sendMessage` queue the message for sending on a background thread and return immediately, which may be more appropriate in a GUI application.

Three callback functions are registered with `theSdk` : these will be discussed later when we look at their implementation.

The next step is to create a new session. This requires three things:
- A session definition
- The URL of a Coordinator where the session will be created
- A set of session options

```c++
arras4::client::SessionDefinition session_def = arras4::client::SessionDefinition::load(SESSION_NAME);
if (NUM_MACHINES > 1) {
    session_def["mcrt"]["arrayExpand"] = NUM_MACHINES;
}
std::string url(COORDINATOR_URL);
arras4::client::SessionOptions options;
```

Session definitions are described in detail [here]({{ "/developer-reference/arras/arras-session-definitions/" | absolute_url }}). This code loads a JSON template from a file and then modifies the number of mcrt computations to match NUM_MACHINES. This doesn't have any effect, given that NUM_MACHINES is set to 1 at the start of the code, but shows how the number of computations would be set in a multi-machine render.

COORDINATOR_URL is hard-coded to "arras:local" at the start of the code, which will cause the client library itself to create the session on the local machine, rather than requesting it from a Coordinator service. 

`SessionOptions` contains information about what is being rendered and by whom : production name, shot, asset, team, and so on. It is used by Coordinator for logging and auditing Arras usage. In this example we will just leave all the fields undefined.

**Session creation**
```c++
std::string sessionId;
try {
    sessionId = theSdk->createSession(session_def, url, options);
} catch (const arras4::sdk::SDKException& e) {
    std::cerr << e.what() << std::endl;
}
if (sessionId.empty()) {
    std::cerr << "Session creation failed" << std::endl;
    return -1;
}
```

If session creation fails, `createSession` will throw an exception. The most likely cause of failure is that the Coordinator cannot find machines to satisfy the requests in the session definition. Creation will also fail if the Coordinator URL is incorrect or if, in local mode, more than one computation is requested.

The session id is a UUID string. It is not directly needed by the client code, but can be used to locate logs and tracking information associated with the session.

When the client code establishes a connection to the session, startup of the required processes is generally still in progress. The client has to wait until this is complete before sending the first message:

**Wait for creation to complete**
```c++
bool ready = theSdk->waitForEngineReady(30);
if (!ready) {
    std::cerr << "Session startup timed out" << std::endl;
    return -1;
}
```

`waitForEngineReady(30)` blocks for up to 30 seconds waiting for startup to complete. You can also use the non-blocking function `isEngineReady()` if it is more appropriate. The best timeout value can depend on the speed of the network and whether you are running in local or distributed mode. A failed startup generally means that one of more of the machines assigned to the session is not functioning correctly.

For this example, we are loading the scene from an RDLA file using the `scene_rdl2` library. If the data is being translated from another format, it will generally be placed into a `scene_rdl2::rdl2::SceneContext` object by code.

**Load scene to render**
```c++
scene_rdl2::rdl2::SceneContext scene;
scene.setProxyModeEnabled(true);
scene_rdl2::rdl2::readSceneFromFile(SCENE_FILE, scene);
```

To start the session rendering, we need to send it an `RDLMessage` with the scene contents. `BinaryWriter` encodes the `SceneContext` as RDLB and places it in a message:

**Send scene to Arras**
```c++
mcrt::RDLMessage::Ptr rdlMsg = std::make_shared<mcrt::RDLMessage>();
scene_rdl2::rdl2::BinaryWriter writer(scene);
writer.toBytes(rdlMsg->mManifest, rdlMsg->mPayload);
theSdk->sendMessage(rdlMsg);
scene.commitAllChanges();
```

Because we set the send mode of `theSdk` to Sync, `sendMessage` will return after sending out the message. As soon as the mcrt computations in the session receive the message, they will start rendering the scene : after an initial "render prep" period, the client will begin to receive messages containing rendered frames.

If the scene changes, we can send updates into the session. Calling `setDeltaEncoding(true)` on the `BinaryWriter` causes it to only encode objects and values that have changed since the last call to `SceneContext::commitAllChanges()`. For purposes of illustration, we'll wait 10 seconds, then load a  "delta" file into the context and send an update.

**Update scene and resend**
```c++
sleep(10);

scene_rdl2::rdl2::readSceneFromFile(SCENE_DELTA_FILE, scene);
writer.setDeltaEncoding(true);
writer.toBytes(rdlMsg->mManifest, rdlMsg->mPayload);    
rdlMsg->mForceReload = false;
theSdk->sendMessage(rdlMsg);
scene.commitAllChanges();
```

Setting `rdlMsg->mForceReload` to false causes the mcrt computations to apply this message on top of the existing scene. To begin afresh with a new scene, we would send a message with `mForceReload = true`.

The final step in the main function is to wait 10 seconds and then terminate the session. Obviously, in practice this would happen when the user requests it, or possibly when the render is complete.

**Shutdown session**
```c++
sleep(10);

theSdk->shutdownSession();
if (!theSdk->waitForDisconnect(30)) {
    std::cerr << "Session failed to disconnect on request" << std::endl;
    theSdk->disconnect();
}
```

`shutdownSession()` is the polite way to terminate a session : Arras will send back a status message with information about the session and then disconnect from the client remotely. If something goes wrong with shutdown -- generally because one or more of the computations has become unresponsive and won't shut itself down cleanly --- the `waitForDisconnect(30)` function will timeout after 30 seconds. Then the client code calls `disconnect()`, which closes the connection from the client end.
## Message Handler

The message handler function is called from a background thread whenever the client receives an incoming message. It begins by identifying the message type and extracting the content:

**Receive message**
```c++
void messageHandler(const arras4::api::Message& msg)
{
    if (msg.classId() == mcrt::ProgressiveFrame::ID) {
        mcrt::ProgressiveFrame::ConstPtr frameMsg = msg.contentAs<mcrt::ProgressiveFrame>();
    }
```
  
ProgressiveFrame messages are sent by the mcrt and merge computations at regular intervals as shading progresses. Each message contains differences from the previous one : [`ClientReceiverFb`](../doxygen-pages/#mcrt_dataioclientreceiverfb) knows how to accumulate these into an image:

**Decode**
```c++
theFbReceiver->decodeProgressiveFrame(*frameMsg, true, [&]() {});
```

If we are using credit messages, an update should be sent back after decoding is complete:

**Credit response**
```c++
 mcrt::CreditUpdate::Ptr creditMsg = std::make_shared<mcrt::CreditUpdate>();
creditMsg->value() = 1;
theSdk->sendMessage(creditMsg);
```

[`ClientReceiverFb`](../doxygen-pages/#mcrt_dataioclientreceiverfb) can provide render progress as a number between 0 and 1. It also provides a status value, which can be `STARTED`, `RENDERING`, `FINISHED`, `CANCELLED`,  or `ERROR`.

**Show status**
```c++
std::cout << "Render progress " << theFbReceiver->getProgress();      
bool frameComplete = theFbReceiver->getStatus() == mcrt::BaseFrame::FINISHED;
```

The current image can be fetched from `theFbReceiver` at any point after the first frame is received. In this case, we wait until the frame is complete before extracting the image as Rgb888 data.

**Handle final image**
```c++
if (frameComplete) {
    std::vector<float> rgbaData;
    theFbReceiver->getBeauty(rgbaData);
    deliverImage(theFbReceiver->getWidth(),
        theFbReceiver->getHeight(),
         rgbaData);
}
```
 
`deliverImage` is left undefined in this example.

`ProgressiveFrame` messages may contain additional images, beyond the beauty image. [`ClientReceiverFb`](../doxygen-pages/#mcrt_dataioclientreceiverfb) provides access to these with `getHeatMap`, `getWeightBuffer` and `getRenderOutput`. The images are also available in *Rgb888* format.

## Status Handler

The status handler function is called when the client receives a status message from Arras. These messages are used to inform the client about events like session shutdown or failure due to error. Clients do not have to define a status handler, but it allows them to report errors to the user.

The status messages are in JSON format, and the field "execStatus" has the current status of the session. If the status is "stopped", then "execStoppedReason" has the reason the session stopped. When a session is ended by a client call to `shutdownSession`, the reason will be "clientShutdown". If the client calls `SDK::disconnect()` then it disconnects before Arras has a chance to send a status message.

```c++
void statusHandler(const std::string& status)
{
    arras4::api::Object statusObject;
    try {
        arras4::api::stringToObject(status,statusObject); 
    } catch(arras4::api::ObjectFormatError& error) {
        std::cerr << "Error parsing status message: " << error.what() << std::endl;
        return;  
    }
    
    arras4::api::ObjectConstRef execStatus = statusObject.get("execStatus",arras4::api::Object());
    if (execStatus.isString() && execStatus.asString() == "stopped") {        
        arras4::api::ObjectConstRef stopReason = statusObject.get("execStoppedReason",arras4::api::Object());
        if (stopReason.isString()) {
            if (stopReason.asString() == "clientShutdown") {
                std::cout << "Session stopped by client shutdown" << std::endl;
            } else {    
                std::cerr << "Session stopped due to " << stopReason.asString() << std::endl;
            }
        }
    }
}
```

## Exception Callback

Incoming messages are handled by a background thread, as are outgoing messages in Async mode. Arras calls the optional exception callback if either of these threads throw an exception. Defining an exception callback function can make debugging easier.

```c++
void exceptionCallback(const std::exception& e)
{
    std::cerr << "Exception: " << e.what() << std::endl;
}
```
## Client Example Code

```c++
#include <mcrt_dataio/client/receiver/ClientReceiverFb.h>
#include <sdk/sdk.h>

#include <scene_rdl2/scene/rdl2/BinaryWriter.h>
#include <scene_rdl2/scene/rdl2/SceneContext.h>
#include <scene_rdl2/scene/rdl2/Utils.h>

#include <message_api/Message.h>
#include <client/api/AcapAPI.h>
#include <client/api/SessionDefinition.h>

#include <mcrt_messages/ProgressiveFrame.h>
#include <mcrt_messages/RDLMessage.h>
#include <mcrt_messages/CreditUpdate.h>

const std::string COORDINATOR_URL("arras:local");
const std::string SESSION_NAME("single_render");
const unsigned NUM_MACHINES = 1;
const std::string SCENE_FILE("example.rdla");
const std::string SCENE_DELTA_FILE("example_delta.rdla");

std::unique_ptr<mcrt_dataio::ClientReceiverFb> theFbReceiver;
std::unique_ptr<arras4::sdk::SDK> theSdk;

void deliverImage(unsigned width, unsigned height, std::vector<float>& rgbaData)
{
}

void messageHandler(const arras4::api::Message& msg)
{
    if (msg.classId() == mcrt::ProgressiveFrame::ID) {
        mcrt::ProgressiveFrame::ConstPtr frameMsg = msg.contentAs<mcrt::ProgressiveFrame>();
        theFbReceiver->decodeProgressiveFrame(*frameMsg, true, [&]() {});

        mcrt::CreditUpdate::Ptr creditMsg = std::make_shared<mcrt::CreditUpdate>();
        creditMsg->value() = 1;
        theSdk->sendMessage(creditMsg);

        std::cout << "Render progress " << theFbReceiver->getProgress();
      
        bool frameComplete = theFbReceiver->getStatus() == mcrt::BaseFrame::FINISHED;
        if (frameComplete) {
            std::vector<float> rgbaData;
            theFbReceiver->getBeauty(rgbaData);
            deliverImage(theFbReceiver->getWidth(),
                         theFbReceiver->getHeight(),
                         rgbaData);
        }
    }  
}



void statusHandler(const std::string& status)
{
    arras4::api::Object statusObject;
    try {
        arras4::api::stringToObject(status,statusObject); 
    } catch(arras4::api::ObjectFormatError& error) {
        std::cerr << "Error parsing status message: " << error.what() << std::endl;
        return;  
    }
    
    arras4::api::ObjectConstRef execStatus = statusObject.get("execStatus",arras4::api::Object());
    if (execStatus.isString() && execStatus.asString() == "stopped") {        
        arras4::api::ObjectConstRef stopReason = statusObject.get("execStoppedReason",arras4::api::Object());
        if (stopReason.isString()) {
            if (stopReason.asString() == "clientShutdown") {
                std::cout << "Session stopped by client shutdown" << std::endl;
            } else {    
                std::cerr << "Session stopped due to " << stopReason.asString() << std::endl;
            }
        }
    }
}

void exceptionCallback(const std::exception& e)
{
    std::cerr << "Exception: " << e.what() << std::endl;
}

int main(int argc, char* argv[])
{
    // Create and initialize SDK object
    theSdk.reset(new arras4::sdk::SDK);

    theSdk->setSyncSend();
    
    theSdk->setMessageHandler(&messageHandler);
    theSdk->setStatusHandler(&statusHandler);
    theSdk->setExceptionCallback(&exceptionCallback);
 
    theFbReceiver.reset(new mcrt_dataio::ClientReceiverFb);

    // Collect creation parameters 
    arras4::client::SessionDefinition session_def = arras4::client::SessionDefinition::load(SESSION_NAME);
    if (NUM_MACHINES > 1) {
        session_def["mcrt"]["arrayExpand"] = NUM_MACHINES;
    }
    std::string url(COORDINATOR_URL);
    arras4::client::SessionOptions options;

    // Try to connect
    std::string sessionId;
    try {
        sessionId = theSdk->createSession(session_def, url, options);
    } catch (const arras4::sdk::SDKException& e) {
        std::cerr << e.what() << std::endl;
    }
    if (sessionId.empty()) {
        std::cerr << "Session creation failed" << std::endl;
        return -1;
    }

    std::cout << "Session created with id " << sessionId << std::endl;

    // We have to wait until the session is ready before sending a message
    bool ready = theSdk->waitForEngineReady(30);
    if (!ready) {
        std::cerr << "Session startup timed out" << std::endl;
        return -1;
    }

    std::cout << "Session is ready" << std::endl;

    // Load a scene and send to session
    scene_rdl2::rdl2::SceneContext scene;
    scene.setProxyModeEnabled(true);
    scene_rdl2::rdl2::readSceneFromFile(SCENE_FILE, scene);

    mcrt::RDLMessage::Ptr rdlMsg = std::make_shared<mcrt::RDLMessage>();
    scene_rdl2::rdl2::BinaryWriter writer(scene);
    writer.toBytes(rdlMsg->mManifest, rdlMsg->mPayload);
    theSdk->sendMessage(rdlMsg);
    scene.commitAllChanges();

    std::cout << "Sent initial scene" << std::endl;
    sleep(10);

    // Load a delta and send
    scene_rdl2::rdl2::readSceneFromFile(SCENE_DELTA_FILE, scene);
    writer.setDeltaEncoding(true);
    writer.toBytes(rdlMsg->mManifest, rdlMsg->mPayload);    
    rdlMsg->mForceReload = false;

    theSdk->sendMessage(rdlMsg);
    scene.commitAllChanges();

    std::cout << "Sent scene delta" << std::endl;
    sleep(10);

    theSdk->shutdownSession();
    if (!theSdk->waitForDisconnect(30)) {
        std::cerr << "Session failed to disconnect on request" << std::endl;
        theSdk->disconnect();
    }

    std::cout << "Session disconnected" << std::endl;
    return 0;
}
```
## Alternative client configurations

It is possible to move some work from the client into computations : either by extending the existing MoonRay computations or adding new ones to the session. For example, you could write a computation to translate from some other scene format to RDLB and place it before the dispatch node, or you could add a computation to translate from ProgressiveFrame format to a regular image or video format. There are a couple of reasons you might want to do this. If both the computations and scene data are in a cloud, then you may want to minimize data transfer between the cloud and client. Rather than loading the scene data into the client, you could send a much smaller "recipe" to construct the scene : the recipe would be evaluated by a computation running in the cloud  to produce the RDLB scene. You might want to add a computation to translate the render results into standard images if, for example, you want the client to run inside a web browser without writing C++ extensions. Of course this could result in a significant increase in data bandwidth from the session back to the client, and would probably not be practical unless the rendered images are relatively small or compressed.


