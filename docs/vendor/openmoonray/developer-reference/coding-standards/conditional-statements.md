---
title: Conditional Statements
---
# Conditional Statements

* For conditional test expressions, use a form that indicates as clearly as possible the types of operands by
avoiding implicit casts.
  + Pointers - don't explicitly compare to `NULL`, because if ptr later changes from a raw pointer to a smart pointer,
this would lead to an implicit cast.
```c++
    // Good:
        if (ptr)

    // Bad:
        if (ptr == NULL)
        if (ptr != NULL)
        if (ptr == 0)
```
  + Numbers
```c++
    // Good:
        if (a == 0)
        if (x > 0.0)

    // Bad:
        if (a)
        if (!a)
```
  + Booleans
```c++
    // Good: 
        if (isValid)
        if (!isValid)

    // Bad:
        if (isValid == false)
        if (isValid == true)
```

* It is preferable to avoid using an assignment within the condition of a conditional statement. But if there is the need for one, it must have no effect in the enclosing scope.
```c++
    // Good:
        if (a == b()) {...}  // standard usage
    
        if (int errorCode = foo()) {  // 0 for success, non-zero for error
            // errorCode is only visible in the scope of the 'if' block,
            // so this is okay
            printError(errorCode);
        }

    // Bad:
        int a;
        if (a = b()) {
            // deceptive (it closely resembles 'a==b()') and also
            // unclear as to whether this is a typo, or intentional
        }
```

* Allow for arithmetic imprecision when comparing floating point values. Use of the equality operator (==) with floats and doubles is often inappropriate. Instead you should compare the values to within a suitable tolerance, which depends on the context. It is helpful to readers of your code if you explain in comments how you arrived at any fixed tolerance value you include. In some special cases == may be the right solution. If so, include comments explaining that this is the case.

* In switch statements, indent case labels at the same level as the associated switch keyword.

* In switch statements, always include a default label, placed at the end.

* In switch statements always comment fallthroughs, or under C++17 use [[fallthrough]]. For example:
```c++
    switch (axis) {
    case 'x':
        position[x] += 100.0;
        // Fallthrough
    case 'y':
        position[y] += 100.0;
        break;
    case 'z':
        break;
    default:
        ASSERT(false, "Illegal value");
        break;
    }
```