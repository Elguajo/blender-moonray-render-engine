---
title: Primitive Types
---
# Primitive Types

* Where it makes sense, avoid writing code that is dependent on the bit size of primitive values.
For code where bit size does matter, use explicit sized types like int32_t. Otherwise use generic types like int.
Be especially cautious about making assumptions about the size of pointers and avoid casting them to
integers - use `intptr_t` and `uintptr_t` if you need to do this.

* Use `size_t` to represent memory size and offsets.

* Don't use unsigned types unless necessary, otherwise it can lead to too many type conversions between signed
and unsigned types.
