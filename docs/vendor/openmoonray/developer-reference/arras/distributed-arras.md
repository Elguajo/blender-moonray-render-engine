---
title: Distributed Arras
---

# Distributed Arras

## Security Note

Since distributed Arras runs services that can read and produce production data, running it in a production environment may require integration with existing infrastructure, and some care regarding security issues. The setup described in this document is a simple one suitable for testing at smaller scale, but you should be aware that the services being started potentially have the ability to execute arbitrary actions (with the permissions of the user running them) on request via a network socket.


## Setup

Distributed Arras requires two programs not used in local mode:

- **Coordinator** is a service that runs once for each "pool" of machines. It is responsible for managing the machines in the pool and allocating work to them.
- **Node** runs on each individual machine in the pool. Coordinator communicates with each Node process.

The OpenMoonRay release contains the Node implementation we use at DWA, called **arras4_node**. The Coordinator we use is a Java service that is tightly coupled to our service infrastructure. We don't think it would be useful to release the DWA Coordinator at this time : instead we provide a Python service called **minicoord**. Minicoord contains most of the same logic as the DWA Coordinator, but is less scalable and robust against network failures.

### Coordinator

The first step in setting up distributed Arras is to start minicoord running on a network machine. This can be one of the pool machines or completely separate. Minicoord requires the python packages `tornado-5` and `requests-2`, so these must be installed somewhere that Python can find them. Minicoord doesn't have any dependencies on the rest of openmoonray, so it can be run outside of a build/release container. The main file is `run.py` : the service runs in the background with a python interpreter in the foreground to inspect the service's current state :

```bash
python -i run.py
```

You should see the status line ``INFO:run:Starting coordinator service on port 8888``. You can change the port used by editing run.py.

### Node

Next you need to run ``arras4_node`` on each pool machine. To start MoonRay sessions, arras4_node needs to be able to find and run a MoonRay/Arras release. If the release is in **${rel_root}**, then the startup commands would be :

```bash
export PATH=${rel_root}/bin:${PATH}
export RDL2_DSO_PATH=${rel_root}/rdl2dso:${rel_root}/rdl2dso.proxy
arras4_node --coordinator-host <coord-host> --coordinator-port 8888 -l 5 --no-consul
```

where **coord-host** is the name of the machine running minicoord. If startup is successful, minicoord should print a message indicating that a new node has registered. ``-l 5`` sets logging verbosity to the maximum level, and ``--no-consul`` is required when using minicoord. The node will allocate all of the machine's CPU cores and available memory to Arras : you can change this using the ``--cores`` and ``--memory`` options. ``arras4_node --help`` prints out all available options.

For testing, you can start multiple **arras4_node** processes on the same machine : minicoord will allocate to them as if each is running on a separate machine. You can even run minicoord, multiple arras4_node processes and arras_render together on a single machine, although the performance may not be very good.

## Testing

You can test the setup using ``arras_render`` to render an RDLA file. The source release contains a minimal RDLA file in **testdata/rectangle.rdla**. To run arras_render, **RDL2_DSO_PATH** must contain at least the proxy scene object SOs, and **ARRAS_SESSION_PATH** must point to a directory containing *.sessiondef* files. A set of these are included in the release, under **sessions**.

```bash
export PATH=${rel_root}/bin:${PATH}
export RDL2_DSO_PATH=${rel_root}/rdl2dso.proxy
export ARRAS_SESSION_PATH=${rel_root}/sessions

arras_render --host <coord-host> --port 8888 --rdl rectangle.rdla -s mcrt_progressive_n --num-mcrt 2 --current-env
```

This should open a window showing the render of red and green triangles. You can rotate the camera by dragging in the window.

`-s mcrt_progressive_n` tells arras_render to use the session definition file **${rel_root}/sessions/mcrt_progressive_n.sessiondef**. This is a simple, general session definition that can run MoonRay on multiple machines, with each render process consuming all remaining cores and memory on the machine. In addition to the moonray computations (named **mcrt_i*N***) there is a process to dispatch the scene (**dispatch**) and a process to merge the results to a single image (**merge**).
The dispatch computation runs by a single thread.
The merge computation runs by multi threads and the best thread count would be depending on the total number of mcrt computations.
Especially, in many mcrt computations cases like 30 or more, merge computation performance would be a bottleneck and it would be better if you can assign as many threads as possible.


There are many other session definitions in the **sessions** directory, but the majority of them deliberately generate errors for testing purposes.

``--num-mcrt 2`` tells arras_render to start two render processes. The session definition ``mcrt_progressive_n`` specifies that each render process uses all the cores available on a machine, so you can increase this number up to the total number of machines running arras4_node. If the number is too high, you will get a message like this:

```bash
2022-08-30T15:15:32.849592 E client[9277]:139684743458816: Unable to connect to Arras: Failed to connect to Coordinator: Insufficient resources available to fill this request
```

The first part of the message is misleading : arras_render did successfully connect to minicoord, but minicoord was unable to satisfy the number of machines requested. You will see similar information output by minicoord itself.

``--current-env`` causes the render processes to inherit their environment from the arras4_node they are running on. It is required for this setup to work.

The ``arras4_node`` processes will generate a lot of log output with the ``-l 5`` setting : you can reduce this by decreasing the number.

You can run ``arras4_render`` in non-gui mode with the ``--no-gui``, but you must then specify a file location for the output with ``--exr <filepath>.exr``. The ``-exr`` flag works with gui mode as well.
