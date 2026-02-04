<!-- To talk about:
    - gcc's willingness to default initialize variables saves us (marked with 🐄)
    - static analysis for uninitialized memory:
        + C++:
            - Impossible with vectors
            - Possible with arrays, gives warning, 🐄
            - Possible with malloc, gives warning
        + C:
            - Possible with malloc
            - Possible with stack, 🐄
        + Constexpr:
            - Not possible in C++ as arrays cannot be Uninitialized
    - Dynamic analysis:
        + asan - does nothing :(
        + msan - memory sanitizer, only available in clang
        + Fuzz testing
            * Not part of OSS fuzz
    - C++ core guidelines:
        + prefer return to output parameters
        + a raw pointer should never enter or leave a function
    - C help:
        + msvc _out_ params (?)
        + [[nodiscard]] for parameters please!
            * A no discard variable is much more challenging to throw away without reading from it. If we had this for parameters (must be used after a function call) this would avoid some issues where a value MUST be read.
        + 
    - 

 -->


<!-- Separated into two talks:
    static analysis
    dynamic analysis
-->

# Mongobleed Static analysis

---

## Rough outline

- MongoDB is a database
- It uses RPC to answer queries
- You can query with compressed JSON
- The error message contains uninitialised data

---

## Compiler warnings:

- Compiler gives relevant warnings

- Modern C++ code tends to initialise memory by default

- Compiler **does** give a warning for un-initialised memory (but that's not in this section)

- Clang tidy doesn't have a check that is relevant.

---

## The code:

```C++
StatusWith<std::size_t> ZlibMessageCompressor::decompressData(ConstDataRange input,
                                                              DataRange output) {
    uLongf length = output.length();
    int ret = ::uncompress(const_cast<Bytef*>(reinterpret_cast<const Bytef*>(output.data())),
                           &length,
                           reinterpret_cast<const Bytef*>(input.data()),
                           input.length());

    if (ret != Z_OK) {
        return Status{ErrorCodes::BadValue, "Compressed message was invalid or corrupted"};
    }

    counterHitDecompress(input.length(), output.length());
    return {output.length()};
}
```

[//]: # (Vertical slide)

Simplifies into:
```C++
mongo::Optional<size_t> DecompressMessage(mongo::ConstDataRange input, mongo::DataRange output)
{
    size_t length = output.length();
    int error_code = Zlib::uncompress(
            output.data_as_byte_ptr(),
            &length,
            input.data_as_byte_ptr(),
            input.length()
        );

    if (ret != Z_OK) { return Optional::Error{}; }
    doLogging();

    return { output.length() };
}
```

[//]: # (Vertical slide)

## Explain ranges/pointers!

- A range (`DataRange`) is a selection or slice into the data stored in an array/list.

- A pointer is a place in memory, they are often used in C to mean arrays, can also be an area a function should write data to.

- Pointers do not have any size and size cannot be attributed to them.

[//]: # (Vertical slide)

We can see that C style code is the issue.

Specifically out pointers/output parameters.

`output` is the output of `uncompress` and `DecompressMessage` but is NEVER a return value.

<!-- This is maybe a bit mean -->

<!-- 
[//]: # (Vertical slide)

### Other notes

- `const_cast` and `reinterpret_cast` are despicable btw
- `reinterpret_cast` is not UB here
- `const_cast` is!!!!
- This is not the correct usage of `DataRange`, it should be `output.data<Bytef>()`
- `DataRange` (publicly) inherits from `ConstDataRange` (data just gets `const_cast`ed a lot)
- Both ranges only hold bytes anyway so what was the point of the `reinterpret_cast`s???

(maybe don't use MongoDB for user data...?)
-->

---

## C++ guidelines

As with most programming languages, outputs should be returned, not used as a parameter.

To combat this MongoDB devs should have written a light, type safe wrapper around ZLib which returns a view!

---

## Output Parameters

There are ways to make [output parameters better](https://www.foonathan.net/2016/10/output-parameter/#) but most are not perfect.

For example [std::outptr](https://en.cppreference.com/w/cpp/memory/out_ptr_t/out_ptr) is a very good way of interacting with C APIs.

[//]: # (Vertical slide)

Output parameters are very common in C:

```C
int do_x(void* something) {
    if (something == NULL) {
        return 1;
    } else {
        *((int*)something) = 1;
        return 0;
    }
}
```

[//]: # (Vertical slide)

```C
int // Error code, what numbers mean are in the documentation
do_x(
    void* something // void* means any type
    )
{
    if (something == NULL) {
        return 1; // Return an error, meaning in docs
    } else {
        // Do something interesting
        *((int*)something) = 1;
        // Don't return it tho (edit in-place instead)
    }
    // No return returns the value at the end of the stack, often 0
}
```

[//]: # (Vertical slide)

Ignoring the value of an out parameter might be valid but in C you'd normally signify this by accepting `NULL` as the input.

In this example we don't accept `NULL` so we expect the output to be used by the caller.

[//]: # (Vertical slide)

Thus we have to write our own check:

I would like to enforce the following:

> After a variable is lent to a function (as a parameter) via non-forwarding, non-const reference or non-const pointer, that parameter must be read before destruction or escape (returned) from the current scope.

[//]: # (Vertical slide)

i.e.
```C++
{
    int i = 0;
    foo(&i);
    // bad
}
```
```C++
{
    int i = 0;
    foo(&i);
    return i; // good
}
```

---

## Semgrep good!


[//]: # (Vertical slide)

Sem grep 1:

Find stack declaration, address of operator in param, then check it's used!
```yml
patterns:
    - pattern-either:
        - pattern: std::out_ptr($PTR, ...)
        - pattern: $FUNC(..., & $PTR, ... )
    - pattern-not-inside: |
        $FUNC(..., &$PTR, ... );
        ...
        $PTR . $ANY ;
    - pattern-not-inside: |
        $FUNC(..., &$PTR, ... );
        ...
        return $PTR;
    - pattern-not-inside: |
        $FUNC(..., &$PTR, ... );
        ...
        $V = $PTR;
```
<small><sub><sup>(Think this could be better btw)</sup></sup></small>

[//]: # (Vertical slide)

This fixes the issue, we can even specify that `$PTR` needs to be something like `size` `length` or `l` with regex.

[//]: # (Vertical slide)

We also could ban defining a function with output parameters to avoid creating bug prone code.

```yml
patterns:
      - pattern-either:
          - pattern: $_ $F(..., $TYPE* $A, ... ) { ... }
          - pattern: $_ $F(..., $TYPE*, ... ) { ... }
          - pattern: $_ $F(..., $TYPE* $A, ... );
          - pattern: $_ $F(..., $TYPE*, ... );
      - pattern-not: $_ $F(..., const $TYPE* $A, ... ) { ... }
      - pattern-not: $_ $F(..., const $TYPE* $A, ... );
```

[//]: # (Vertical slide)

And we can test out semgrep checks:
```C++
```

[//]: # (Vertical slide)

Leading to a possible fix:

```C++
StatusWith<std::size_t> ZlibMessageCompressor::decompressData(ConstDataRange input,
                                                              DataRange output) {
    std::size_t length = output.length();
    int ret = ::uncompress(
                    output.data<Bytef>(),
                    &length,
                    input.data<Bytef>(),
                    input.length()
        );
    output.length() = length;

    if (ret != Z_OK) {
        return Status{ErrorCodes::BadValue, "Compressed message was invalid or corrupted"};
    }

    counterHitDecompress(input.length(), output.length());
    return {output.length()};
}
```
