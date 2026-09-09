---
title: Miscellaneous
---
# Miscellaneous

* When the return value of an increment/decrement operation is not used, prefer pre-increment/pre-decrement.
Some types (e.g., iterators) incur overhead in post-increment as a copy is required to be made, and in general,
the compiler is unable to optimize this copy away. Post-increment is a source of premature pessimization.
```c++
for (int i = 0; i < n; ++i) { // Prefer pre-increment
    ...
}
```

* Don't use pointers to run through arrays of non primitive types. Use explicit array indexing, iterators or
generic algorithms instead.

* Prefer C++ casts to C casts.
```c++
// Good:
    static_cast<int>(theFloatValue)
// Bad:
    (int)theFloatValue
```

* Library code must never deliberately terminate the application in response to an error condition. If the library
cannot safely continue, consider throwing an exception instead. You should attempt to document any cases where a
call in your library may result in an exit (for example, through a non-conforming library).

* Prefer smart pointers over new/delete and  malloc/free.

* Use of the C++ Standard Template Library is encouraged. Internally developed classes that implement similar
functionality should clearly document why the corresponding STL classes were not used.

* Avoid goto.

* Avoid "magic numbers". Use symbolic constants
  + to make the meaning clear, e.g.
```c++
    if (delta < NR_ERROR_TOLERANCE)
```
  + to ensure that if the value is ever changed, it changes everywhere consistently:
```c++
    char buffer[MAX_PATH_SIZE];
    if (bufferIndex >= MAX_PATH_SIZE)
```

* Use literals where these don't apply, for example:
```c++
    if (polygon.getVertexCount() == 3) {
        processTriangle(polygon);
    }
```

* If you use typeid/typeinfo, be aware that although all runtimes support `typeinfo::name()`, the format of the
string it returns varies between compilers and even for a given compiler the value is not guaranteed to be unique.

* When overriding virtual functions, use `override` and drop the `virtual` keyword. The `override` keyword avoids
name-hiding mistakes and ensures that overridden functions are properly called virtually. As the `override` keyword
only works for virtual functions, the `virtual` keyword is not required and is redundant.
```c++
class Base
{
public:
    virtual void f() = 0;
};
class Derived : public Base
{
public:
    void f() override;
};
```