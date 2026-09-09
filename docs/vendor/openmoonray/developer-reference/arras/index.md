---
title: Arras Overview
---

# Arras Overview

Arras creates processes that perform work for an application. The individual processes are called ***computations***, and a set of computations created for a specific task (such as rendering a scene) is called a ***session***. Computation processes within the same session can communicate with each other by sending messages. The computations in a session generally span multiple machines, and messages are sent between them using network sockets.

This is a diagram of a typical multi-machine rendering session:

![Arras Session Diagram](../../assets/images/developer-reference/arras/arras-session-diagram.png)



Each of the orange boxes is a computation. The four "render" computations (we call this computation as "**mcrt**" computation) are all rendering the same scene, and will normally be placed on different physical machines. "dispatch" handles dispatching the scene description to each render, and "merge" merges the rendered outputs into a single image. Dispatch and merge will usually be placed on the same machine as one of the mcrt computations. Arrows between the boxes represent messages.

The ***client*** is similar to the computations, in that it sends and receives messages. Unlike the computations, it is not created by Arras : it is part of the application that is using Arras. The client code begins by asking Arras to create a session : Arras responds with a network connection that the client can use to send to and receive from the session. Then the client starts sending input data to the session in the form of messages, and receiving results (also as messages). A client application can have any number of sessions running at any one time.

## Coordinator and Node

The computation processes are created and managed by a pair of services : ***Coordinator*** (running just once for each pool of machines) and ***Node*** (running on each machine in the pool).

Coordinator is responsible for tracking the currently active sessions (from all clients), and how many resources (CPU cores and memory) are in use on each machine. Node is responsible for local operations on each machine, like starting and stopping each computation.

Clients create a new session by sending a request to the Coordinator service. Coordinator tries to allocate the requested computations to machines with sufficient remaining resources. If it succeeds, it responds to the client with the identity of one of the allocated machines (called the ***entry node***). At the same time it sends requests to the Node services on each allocated machine, asking them to start running their assigned computations. Coordinator monitors the progress of session startup and, once everything is running, notifies the client that it may begin sending input data to the entry node.

## Local Mode

The Arras client library can create a single computation process on its local machine without going through Coordinator or Node. This creates a "local mode" session, that doesn't require any external services to be running. The client interface to a local mode session is essentially the same as to a distributed session, except that the client can only request one computation.

## Messages

Arras messages can vary in size from a few bytes for a control message asking a computation to pause, to multiple gigabytes for a large scene description. The message types that carry a lot of data are optimized for size, and typically have a "delta" form that carries just the differences from the last message of the same type. For this reason Arras never drops messages deliberately : if a message cannot be delivered for any reason, the session is terminated.

Problems can occur if a computation sends out messages at a greater rate than they can be transmitted and handled. The messages are buffered, and ultimately delivered, provided that the buffering capacity is not exceeded. However there can be an increasing latency between when the messages are sent and when they are processed by a receiver. Since messages cannot be dropped, it is necessary for the source computation to reduce the rate at which it is sending out data. The issue can be dealt with by sending a "credit" message back from the receiver to the source indicating that a message as been processed. The source computation will not send the next message if it has insufficient credit, preventing it from getting too far ahead of the receiver.

When the client sends new input data into a session, it may continue to receive results based on the previous input for a time, due to latency in the system. Each source input message contains a unique source id which is copied across to any output messages based on that input. The client can identify the first output message corresponding to an input change by examining the source ids.

Messages have types : for example "RDLMessage" is the type of messages used to send RDLB format scene descriptions to mcrt computations. Computations normally determine how to handle an incoming message based on its type.

The Arras message API is used to define new message types. Each new type must define serialization and deserialization functions to convert between its in-memory representation and the bytes sent to transmit it over a socket.

## Computations

Computation processes use an executable called ***execComp***. execComp handles initial startup of the computation, connection to Node (or the client, when using local mode), and serialization/deserialization of messages. The actual work of a computation is performed by a shared library loaded by execComp. These shared libraries are often referred to as the computations. The shared libraries used by MoonRay computations are as follows:

```
    dispatch     libcomputation_progmcrt_dispatch.so
    mcrt         libcomputation_progmcrt.so
    merge        libcomputation_progmcrt_merge.so
```

Computation dsos use the Arras computation API. A dso needs to provide a message handler function, which execComp calls with the deserialized form of each incoming message. The API provides a send function that the computation code calls for outgoing messages. Computation dsos also provide a configure function, that is called with parameters defined in the session definition.

## Clients

Arras clients are written using the Arras client API. Message handling using the client API is very similar to the computation API. When creating a new session, the client has to supply a session definition, listing the required computations, and the URL of a Coordinator service. If allocation of the processes is successful, Coordinator replies with a connection address. This is the address of a socket owned by the Node process on one of the machines allocated to the session -- called the *entry node* of the session. The client can connect almost immediately, but has to wait to receive a "ready" message before beginning to send input to the session. To terminate the session, the client sends a "shutdown" message.

When using local mode, the client substitutes "local:" for the Coordinator URL. The client API then emulates Coordinator, allocating a single computation on the local machine.

Arras client code can be written as a standalone application, or as a plugin to a DCC. The MoonRay computations expect to receive scene descriptions in RDLB format, so the client code has to translate from the DCC's native format. Rendered images are returned by the session in a compressed format called ProgressiveFrame : MoonRay provides a library to decode these into standard image formats.

A client can start and maintain any number of different sessions : each session can render one scene at a time.

