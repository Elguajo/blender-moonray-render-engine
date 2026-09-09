---
title: Singletons
---
# Singletons

* Declare instance, rather than class, members and methods where possible. This both makes it easier to change to
a multiple instance design later and permits polymorphic subclassing (remember, static methods can't be virtual).
In essence, use singletons instead of statics when possible for 'globalesque' stuff.

* Maintain a private static class pointer variable, `sSingleton`.

* Provide a static class method, `singleton()`, that initializes the singleton and returns a reference to it.
This method throws an exception if the singleton cannot be created. Each class decides whether subsequent calls
to `singleton()` reattempt to initialize the singleton, return the already initialized instance, or just throw
an exception.
