---
title: Exceptions
---
# Exceptions

* The use of exceptions is encouraged for error handling.

* Only use exceptions for unusual or erroneous situations. Do not use them as a conditional mechanism during regular
execution. Knowing when to use exceptions is a matter of judgment. Remember that when an exception actually gets
thrown it can have a significant performance impact. Here are some examples of good use of exceptions:
```c++
class Foo
{
    void doSomething(Foo* aFoo)
    {
        if (!aFoo) {
            throw(except::ValueError, "Valid foo pointer required"));
        }
        aFoo->doSomethingElse();
    }
};
class Bar
{
    void writeIntToFile(const char* aFileName, int anInt)
    {
        ofstream theFile(aFileName);
        if (!theFile) {
            throw(except::IoError, "Unable to open file:" << aFileName);
        }
        theFile << anInt << ends;
        theFile.close();
    }
};
```
* Header files must document which exceptions are thrown using comments:
```c++
class Foo
{
    /// @throw ValueError if ptr is illegal
    void doSomething(Foo* ptr);
};
```
* Methods must declare all exceptions they might throw using comments, but not exception specifications, i.e. use of
the C++ exception specification mechanism should be avoided.
(See [this article](http://www.gotw.ca/publications/mill22.htm) ).

* Do not use an empty exception declaration, as in `throw()`. Use `noexcept` instead.

* Throw scope local exception instances, not pointers or references or globals.

* Catch exceptions by reference.

* Never allow an exception to escape from a destructor. This not only means that the destructor exits before it
is finished, potentially leaving a partially destructed object, but it can also create a "nested" exception
situation when a destructor is called during unwinding of the stack due to another exception.
