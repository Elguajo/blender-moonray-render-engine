---
title: Formatting
---
# Formatting

The fundamental rule when modifying an existing source file is to adopt the prevailing style used in that source file.
Non-conforming code can be reformatted to meet the standard, but such a change should be performed as an independent git
commit. The formatting standards are intended to give our code a consistent look and thereby make it easier to read.
You may break any of these formatting rules only in cases where following the standard severely impacts code
readability. Such cases should be rare and easily agreed upon by both programmer and code reviewer.

* The maximum line length is 120 characters. The goal of this standard is to be shorter, but not too much shorter, than
the maximum line length displayable in the github difftool.

* Indentation is 4 spaces. Do not use tabs.

* If a function's list of parameters must be split across multiple lines, indent new lines to line up with the first
character following the opening parenthesis. In cases where parameters are strongly related (e.g. `int x, int y`) prefer
to group those parameters on the same line.

* If a conditional expression must be split across multiple lines, indent new lines to line up with the first character
following the opening parenthesis.

* Include the standard copyright notice at the top of all files:
```c++
// Copyright 2023-2025 DreamWorks Animation LLC
// SPDX-License-Identifier: Apache-2.0
```

* Items in all files should be in the following order:
  1. copyright notice
  2. include statements
  3. constants
  4. typedefs, including structures
  5. class definitions
  6. function prototypes
  7. function/method implementations

* Leave a blank line between a group of variable declarations and other code. e.g.
```c++
{
    int x;
    int y;

    x = base.x + dx;
    y = base.y + dy;
}
```

* Leave a space after the keywords `if`, `switch`, `while`, `do`, `for`, and `return` (assuming the function returns a
value).

* Leave a space on each side of binary operators (such as `+`, `-`, `*`, `/`, `&&`, and `||`). For clarity in compound
expressions, you may omit the spaces on either side of `*` and `/` operators to illustrate their precedence over `+` and
`-`. e.g.
```c++
float y = a*x*x + b*x + c;
```

* Do not leave a space between any dereferencing operator (such as `*`, `&`, `[]`, `->`, or `.`) and its operand. Note
that this only applies to operators in expressions, not to type declarations, and in particular the location of the `*`
in the declaration of pointers is left up to the developer. e.g.
```c++
{
    Point* thePoint;
    int *r, *g, *b;

    r = &(thePoint->x());
    g = &(thePoint->y());
    b = &(thePoint->z());
}
```

* However, do not mix pointer and non-pointer definitions in the same statement:
```c++
int* p, q;  // BAD. It is not immediately clear that p is a
              // pointer but q is an int
```

* In argument lists, leave a space after each comma.

* Do not leave a space after an opening parenthesis or before a closing parenthesis.

* Do not leave a space before an end-of-statement semicolon.

* Parentheses should be used to clarify precedence in expressions. You should not assume that the person reading your
code remembers the precedence rules beyond `*` and `/` over `+` and `-`.

* Do not use literal tabs in strings or character constants. Rather, use spaces or \t.

* If an argument list is too long, break it between arguments. Group related arguments on lines if appropriate.

* Modified spacing is allowed to vertically align repetitive expressions. e.g.
```c++
v3dSet(-1.0, -1.0, -1.0, minCoords);
v3dSet( 1.0,  1.0,  1.0, maxCoords);
```

* Always begin numeric constants with a digit (e.g., 0.001f not .001f).

* K&R-style brace placement must be used in public code (e.g. all code checked into the repository). This means the `{`
goes on the end of the line for flow control statements and on a line by itself for function, class and structure
definitions. Examples:

  + if format:
```c++
if (isNull(foo)) {
      // Code...
} else if (isNull(bar)) {
      // Code...
} else {
      // Code...
}
```

  + for format:
```c++
for (int i = 0; i < number; ++i) {
      // Code...
}
```

  + while format:
```c++
while (i < 0) {
      // Code...
}
```

  + do-while format:
```c++
do {
      // Code...
} while (i < 0);
```

  + switch format:
```c++
switch (value) {
case A:
      // Code...
    break;
case B:
      // Code...
      // Use the following keyword to denote that
      // you want the fallthrough behavior of switch:
      // Fallthrough
default:
      // Code...
      // Always have a default, even if there's no code.
}
```

  + class/struct format:
```c++
class
{
public:
      // Public member functions
private:
      // Private member functions and data members
};
```

  + Function format:
```c++
int foo(int a)
{
      // Code...
}
```

  + try/catch format:
```c++
try {
      // Code...
} catch (...) {
      // Code...
}
```

* Do not place the body of a conditional on a second line without using braces, since this might cause a mistake later
if a programmer tries to place additional statements in the body. e.g.
```c++
if (a <= maxPermittedValue)
    processSomeThing(a);  // WRONG!
```

