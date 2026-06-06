
# Intro To Templates

The original generics

---

- We often want code to be as reusable as possible
- e.g. we don't want to write, `is_even`, for ints, unsigned ints, longs, unsigned longs, floats, doubles, long doubles, int_ptr,fractions, decimals/big numbers, complex numbers, element-wise vectors/simd vectors, unit types, strong types, pointers to above values, ...
<!-- .element: class="no-wrap" -->
- We want `is_even` to take (almost) anything and do something with it
- If it can't do something reasonable, we want to compile error

[//]: # (Vertical slide)

```C++
constexpr bool is_even(const int to_check) { return to_check % 2; }
constexpr bool is_even(const std::int_ptr to_check) { return to_check % 2; }
constexpr bool is_even(const unsigned int to_check) { return to_check % 2; }
constexpr bool is_even(const long to_check) { return to_check % 2; }
constexpr bool is_even(const unsigned long to_check) { return to_check % 2; }
constexpr bool is_even(const float to_check) { return to_check % 2; }
bool is_even(const double to_check) { return is_even(static_cast<int>(to_check)); }
bool is_even(const long double to_check) { return is_even(static_cast<int>(to_check)); }
bool is_even(const std::float16_t to_check) { return is_even(static_cast<int>(to_check)); }
bool is_even(const std::float32_t to_check) { return is_even(static_cast<int>(to_check)); }
bool is_even(const std::float64_t to_check) { return is_even(static_cast<int>(to_check)); }
bool is_even(const std::float128_t to_check) { return is_even(static_cast<int>(to_check)); }
bool is_even(const std::bfloat16_t to_check) { return is_even(static_cast<int>(to_check)); }
```

But maybe you think this is okay:
- maybe we do want to handle floating point values differently to integers
<!-- .element: class="fragment" -->
- maybe we do need a function for each one
<!-- .element: class="fragment" -->
- maybe we never do something as complex as check if a value is even
<!-- .element: class="fragment" -->
- maybe we haven't seen the bug yet
<!-- .element: class="fragment" -->

---

## Template syntax

The `template` keyword has arguments that can be types or non-types (values)
Like any other argument, these can be defaulted
<!-- .element: class="fragment" -->
If the argument is a value, like any other argument, we need to tell the compiler what type the value is
<!-- .element: class="fragment" -->
If the argument is a type we also need to tell the compiler. This can be done with the `class` or `typename` keywords
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

```C++
template<typename T>    anything;
// Is equivalent to
template<class T>       anything;

template<class T>         T foo();
// Requires explicit type in the call
foo<int>();
// Whereas
template<class T = int>   T bar();
// Can be called with
bar(); /*OR*/ bar<>();
```

[//]: # (Vertical slide)

We can also specify values, this can be seen most commonly in `std::array`
```C++
template<typename T, size_t S>
class MyArray;

auto large_array = MyArray<int, 1024u>{};
```

---

## Function templates

A function template, or templated function,
<!-- .element: class="fragment" -->
is a function
<!-- .element: class="fragment" -->
and a template
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

We can simplify our `is_even` functions down to simply take **anything**, then try to do a modulo 2 on the argument.

Then for anything that has a modulo operator, we can check if it's even or not

[//]: # (Vertical slide)

```C++
[[nodiscard]] constexpr template<typename I>
bool is_even(const I& to_check) { return to_check % 2; }
```

So these calls will compile:
```C++
is_even(10); is_even(100); is_even(101); is_even(1024u);
is_even(std::chrono::milliseconds{10});
```

[//]: # (Vertical slide)

Note: In C++ 20 we can specify that a function argument is a template with the `auto` keyword:
```C++
[[nodiscard]] constexpr
bool is_even(const auto& to_check) { return to_check % 2; }
```

[//]: # (Vertical slide)

We haven't explicitly supported floats, they will still work because of implicit conversions 🤮🤮

We can avoid them by adding a float template first:
```C++
bool is_even(const auto& to_check) { return std::round(std::fmod(to_check)) == 0.0; }
```
(or delete non-explicit overloads `auto is_even(auto) == delete;`)
<!-- .element: class="fragment" -->
(or use concepts, see later)
<!-- .element: class="fragment" -->

---

## Class templates

A class template, or templated class,
<!-- .element: class="fragment" -->
is a class
<!-- .element: class="fragment" -->
and a template
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

Say we want to write a custom Queue, 
we could write one for each type we need:
char, unsigned char, short, unsigned short, int, unsigned int, long, unsigned long, long long, unsigned long long, float, double, long double, 
<!-- .element: class="no-wrap fragment" -->
We could instead write a generic class
<!-- .element: class="no-wrap fragment" -->

[//]: # (Vertical slide)

```C++
template<typename T>
class Queue {
    // We can use T
    // the same as any other argument
    // (by name)
    std::array<T, S> holder;
};

```
