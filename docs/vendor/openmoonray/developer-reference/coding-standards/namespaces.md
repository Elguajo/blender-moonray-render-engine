---
title: Namespaces
---
# Namespaces

* Namespaces should always be used. The `main()` function is the only exception. This is to avoid conflicts in the
global namespace which can be particularly painful to resolve when using third-party libraries.

* Do not use anonymous namespaces in header files, where they are at best useless, and at worst lead to undefined
behavior.

* Libraries must declare their structures and functions in a namespace (the "library namespace") that matches the
library's name. If necessary, library internals can be placed within an internal namespace nested within the library
namespace (e.g. `gmath::internal`). For consistency, such namespaces should be called "internal". Apart from this, the
use of nested namespaces should be avoided.

* Avoid the use of `using namespace` in header files. This defeats the point of namespaces and may cause problems in
the future should additional symbols get added to the included namespace.

* `using` declarations are allowed for individual symbols (e.g., `using std::vector;`), but they should never appear
in a header file. Putting a using declaration in a header file means that everybody that uses the header file will
also be forced to use the declaration. Keep them in the body where they won't bother anyone else, and even then, only
after all of the `#include` directives.

* Define global operators in the namespace of their parameters. You can't specify the namespace of an operator when
you're using it, so the compiler will automatically check the namespaces of any operator arguments.

* Namespaces are not indented.
