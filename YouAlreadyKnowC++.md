
# You already know C++

C is bad. The best and worst part of C++ is it's compatibility with C.

[//]: # (Vertical slide)

This means we inherit the best parts of C and the worst.

However C++ is good and offers the high level, safe alternatives we've come to expect from languages.
I'll show you what these are, where to find them and how C++ is simpler than you probably gave it credit for.

---

## C is evil

In C the programmer is required to keep track of all heap storage, i.e.:
- Before usage size must be allocated
- This size cannot change
- Must be freed when done with
- Cannot be used again after free

Modern languages handle all this for us, C++ offers all common data structures without need to mess with memory.

---

## How to be safe

Use the standard library.

[//]: # (Vertical slide)

Most common problems people have can be solved by using the standard library:
- Buffer overflow? Use `std::vector` and `std::string`.
- Use after free? Use a vector `std::unique_ptr` or `std::shared_ptr`.
- Access out of bounds? Use bound checked lookups like `.at(size_t)`
- Iterating through a container? use `for (auto item : container)`

[//]: # (Vertical slide)

The vast majority of unsafe code does things in a C style rather than a C++ style. For example it is unlikely that a file handle would be leaked with C++'s `std::ostream` and much more likely with C's `fopen`.

---

## Still struggling? WWPD

**W**hat **W**ould **P**ython **D**o?

I think python and C++ are very similar and I think good C++ should resemble python.

For example our python code for creating a list of size 10 containing 0 (`ints`):

```python
import ctypes
size_t = ctypes.c_size_t
int32 = ctypes.c_int32
size_of_list = 10
size_of_list_bytes = size_t((32//8) * size_of_list)
libc = ctypes.CDLL("libc_malloc_debug.so")
data_ptr = libc.malloc(size_of_list_bytes)
```
<!-- .element: class="unknown" wants="run" -->

[//]: # (Vertical slide)

No?

You don't write python like that?

Then why write C++ like that?

[//]: # (Vertical slide)

- I need an array `A` with 10 `ints` inside, all 0?

```py
A :list[int] = [0] * 10;
```
```C++
std::array<int, 10> A{0};
```

[//]: # (Vertical slide)

- Okay but I need it to be resizable.
```py
A :list[int] = [0] * 10;
```
```C++
std::vector<int> A(10, 0);
```

[//]: # (Vertical slide)

- Cool now how do I iterate through it?
```py
for a in A: code(a)
```
```C++
for (auto a : A) { code(a); }
```
<sub><sup>Where `auto` is "any type, IDC"</sup></sub>

[//]: # (Vertical slide)

- How do I delete the memory so I don't leak it?

```py
# nothing
```
<sub><sup>(Garbage collector handles it)</sup></sub>

```C++
/* nothing */
```
<sub><sup>(Item leaves the stack and destructor handles it)</sup></sub>

---

## When you can't use std

Usually because the input is different to the standard, such as a `char*` instead of a `std::string`.

<sub><sup>There are other reasons, some valid, but advice is similar regardless.</sup></sub>

[//]: # (Vertical slide)

### Bad input

If you are given a char pointer (`char*`) rather than a string (also known as a CString) and not something like `std::string` you should get it into something "known safe" as soon as possible.

For our purpose we will use `std::string`.

This means you'll need to check the length of it.

[//]: # (Vertical slide)

In C the length of a string is from the first character to the first string termination character (`\0`).

So to check the length you have to loop through it.

Checking each character to see if it is `\0`.

[//]: # (Vertical slide)

A common issue occurs when using:
```C++
size_t strlen(const char* str)
```
Which will happily go forever and read out of bounds if string termination character is not found.

[//]: # (Vertical slide)

If the length of the buffer (where the string is held) is known we can use that to limit how far we look for the null terminating character with
```C++
size_t strnlen_s(const char* str, size_t max_length)
```

[//]: # (Vertical slide)

Now we know the string is safe and we have the length of the string we can copy it into something less cumbersome to deal with like a `string` or a `string_view` (assuming we know the lifetime of the object).

---

## But UB?

If you've done something wrong the compiler is likely to tell you about it or at least be able to tell you about it.

To be told about more possible things you've done wrong enable more compiler warnings.

[//]: # (Vertical slide)

For example this code compiles with no warnings on gcc but when ran, crashes because of an infinite loop.
```C++
template <typename T>
struct C {
    void foo() { static_cast<T*>(this)->foo(); }
};

struct D : C<D> { };

void f(D& d) { d.foo(); }

int main() {
    D d{};
    f(d);
}
```
<!-- .element: class="erroring" wants="run" -->

[//]: # (Vertical slide)

We can let gcc know that actually we maybe want to be warned about such silliness with the flag
```
-Winfinite-recursion
```
or another one that includes it such as
```
-Wall
```

[//]: # (Vertical slide)

This gives us the output:
```
<source>: In member function 'void C<T>::foo() [with T = D]':
<source>:3:10: warning: infinite recursion detected [-Winfinite-recursion]
    3 |     void foo() { static_cast<T*>(this)->foo(); }
      |          ^~~
<source>:3:44: note: recursive call
    3 |     void foo() { static_cast<T*>(this)->foo(); }
      |                  ~~~~~~~~~~~~~~~~~~~~~~~~~~^~
```

[//]: # (Vertical slide)

To force colleagues to listen to these use: `-Werror` or if the code is already filled with warnings turn some into errors with `-Werror=XXX` and hide it in the build script so they can't turn it off.

---

## But UB!

UB is short for undefined behaviour, this is something that the C++ standard (usually intentionally and explicitly) has not specified, usually because it would force a compromise onto the user.

[//]: # (Vertical slide)

For example if I add two numbers and attempt to store the result in a space that is too small to store that number I can:
[//]: # (Vertical slide)
1. Store the result in a larger amount of memory, check if it's bigger than max of the small amount of memory, crash or put it in the smaller bit of memory.

i.e. short + short = long; if long > max_short : crash, otherwise cast; return;

[//]: # (Vertical slide)
2. Use some CPU trickery to set a flag if an overflow has occurred

i.e. short + short = short; if not did_this_work() : throw (or something)

[//]: # (Vertical slide)
3. Do all maths with dynamically sized storage and grow it if required

(what python does)

[//]: # (Vertical slide)
4. Do a saturated add

short A + short B = short; if A + B > max_short : return max_short

(but often quicker)

[//]: # (Vertical slide)
5. Do an overflow

short + short = short; return short % max_short

[//]: # (Vertical slide)

In 1 we slow the code down (a little, mostly through register contention), in 2 we limit compilation to CPUs with this special magic, in 3 we limit ourselves to processors with dynamically resizable memory (no GPUs), 4 and 5 make enforcements on the processor that might benefit one but be terrible for another (cannot mask int maths as float maths on certain GPUs)

[//]: # (Vertical slide)

So the C++ committee made the decision to make no decision.

You can run your code with UB sanitizers, this means that any code that executes UB will cause a crash. In gcc it's two lines.

[//]: # (Vertical slide)

### But Rust!

For this example Rust crashes on debug but overflows on Release, it's effectively the same as C++ but with slower int maths on some GPUs (compromise 5).

---

## BUT UB!!

Still not convinced?

The `constexpr` keyword was introduced in C++11 and runs code at compile time*. Any code ran at compile time cannot execute undefined behaviour, so will result in a compilation failure if attempted. So any code you can test at compile time is guaranteed to not contain undefined behaviour.

[//]: # (Vertical slide)

```C++
#include <limits>
int main() {
    constexpr auto max_int = std::numeric_limits<int>::max();
    constexpr auto i = max_int + 1;
}
```
<!-- .element: class="unknown" wants="compile-error" -->

Gives error:
```
error: overflow in constant expression [-fpermissive]
```

[//]: # (Vertical slide)

Whereas the non-constexpr version will compile
```C++
#include <limits>
int main() {
    auto max_int = std::numeric_limits<int>::max();
    auto i = max_int + 1;
}
```
<!-- .element: class="unknown" wants="compiles" -->

<sub><sup>(and invoke UB at runtime)</sup></sub>

[//]: # (Vertical slide)

\* Technically `constexpr` code must run any time before the program runs, so on embedded devices this might be on device start but realistically it's at compile time.

Again the standard is written this way to allow for different processors to handle things differently, for example if I am compiling for some processor that has much more precise float handling, I probably don't want to use the processor I am compiling the code with to do all my maths.

---

## But garbage collection?

---

### Functions:
We know that any object going into a function as an argument has a lifetime greater than the local scope of the function.

```C++
void foo(int& in) {
	// We know that in is always valid in this scope
	in += 1;
}

int main() {
    // We know that a is always valid in this scope
    int a = 1;
    foo(a);
}
```
<!-- .element: class="unknown" wants="runs" -->
Here `a` goes through `foo` as argument `in`, we know the whole time it's safe.


[//]: # (Vertical slide)

Following the above statement, we (and the compiler) know that any local data inside the function we want to end up outside of the local scope __must__ be __moved__ (or copied) to that outer scope.

So `return` **must** do a move or copy
```C++
int foo(int& in) {
	int i = 1;
	return i; // (free) Implicit move
}
```

[//]: # (Vertical slide)

Or a copy if object is not movable
```C++
struct NoMove {  NoMove(NoMove&&) = delete; };
NoMove foo() {
	return NoMove{}; // Implicit copy (cannot move because we deleted it), (also usually free)
}
```

[//]: # (Vertical slide)

If we do something silly to avoid this, like:
```C++
int& foo() { return 1; }
```
<!-- .element: class="not-compiling" wants="compile-error" -->
the compiler errors. 

[//]: # (Vertical slide)

If we are more determined about our silliness,
```C++
int& foo() { int i = 0; return i}
```
the compiler warns us:
```
warning: reference to local variable 'i' returned [-Wreturn-local-addr]
   10 | int& foo() { int i = 0; return i; }`
	  |                                ^
```
So naturally, use `-Werror=return-local-addr` (forced in C++26)

---

Leveraging this idea we can create a guideline:

> A function should return an owning object.

[//]: # (Vertical slide)

Though sometimes we want to return references so lets amend it:

> Functions that return a reference should delete the appropriate overloads where the object they are referencing goes out of scope.

[//]: # (Vertical slide)

```C++
#include <vector>
int& GetGreatest(std::vector<int>& input) {
    int max = 0;
    size_t index_of_max = 0;
    size_t i = 0;
    for (auto& value : input) {
        if (max > value) {
            max = value;
            index_of_max = i;
        }
        ++i;
    }
    return input[max];
}

int main() {
    std::vector<int> input{1,2,3,5};
    int& greatest = GetGreatest(input);
}
```
<!-- .element: class="compiling" wants="compiles" -->
Returns a reference to an object that was in the input vector

[//]: # (Vertical slide)

We can normally see structs (or classes) as a very similar extension of this concept:
```C++
struct IntRefWrapper {
    IntRefWrapper(int& wrappedInt) : m_wrappedInt{wrappedInt} {}
    int& m_wrappedInt;
};

int main() {
    int a = 1;
    IntRefWrapper b{a};
}
```
<!-- .element: class="unknown" wants="running" -->

---

# Forcing Correct Scope

[//]: # (Vertical slide)

A forwarding reference can be taken, as an argument, using a const reference. This can produce a scope issue where the rvalue goes out of scope before the returned reference:

```C++
#include <vector>
const int& first(const std::vector<int>& v) { return v.front(); }

int main() {
    {
        std::vector<int> vec{1,2,3,4};
        auto& first_ = first(vec); // No scope issues
    }
    auto& first_ = first({1,2,3,4}); // Compiles but UB
}
```
<!-- .element: class="unknown" wants="compiles" -->

[//]: # (Vertical slide)

We can force this to be a compile error by deleting the overload:

```C++
#include <vector>
const int& first (const std::vector<int>& v) { return v.front(); }
auto first(std::vector<int>&&) = delete;

int main() {
    auto& a = first({1,2,4}); // doesn't compile
}
```
<!-- .element: class="unknown" wants="compile-error" -->

[//]: # (Vertical slide)

Similarly we can do this for classes.
```C++
struct S {
    int& GetA() & { return A; } // Caller can edit A
    int& GetA() && = delete;    // Caller shouldn't edit A, bug?

    const int& GetA() const & { return A; } // Caller can't edit A
    const int& GetA() const && = delete;    // bug?
    int A;
};

int main() {
    // S{}.GetA(); // Errors
    { S s{};        s.GetA() = 1; } // Compiles
    { const S s{};  s.GetA();     } // Compiles
}
```
<!-- .element: class="compiling" wants="compiling" -->

<sub><sup>most useful if doing something on a getter</sub></sup>
