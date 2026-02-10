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
<!-- .element: class="r-fit" -->

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

    if (ret != Z_OK) { return mongo::Optional::Error{}; }
    doLogging();

    return { output.length() };
}
```
<!-- .element: class="r-fit" -->

---

## Explain ranges/pointers!

- A range (or a view) (`DataRange`) is a selection or slice into the data stored in an array/list.

- A pointer is a place in memory, they are often used in C to mean arrays, can also be an area a function should write data to.

- Pointers do not have any size and size cannot be attributed to them.

[//]: # (Vertical slide)

There are many reasons to use views/ranges. One is speed but more commonly we use them for dependency inversion:

- If we know where data starts, ends and that it's contiguous; if the container is an array or a vector is irrelevant.

- If an object is small enough to be stored in registers, it is quicker to copy it than use a reference. This is rarely relevant though.
<!-- .element: class="fragment" -->

---

```C++
size_t length = output.length();
int error_code = Zlib::uncompress(
        output.data_as_byte_ptr(),
        &length,
        input.data_as_byte_ptr(),
        input.length()
    );
if (ret != Z_OK) { return mongo::Optional::Error{}; }
doLogging();
return { output.length() };
```

We can see that C style code is the issue.
<!-- .element: class="fragment" -->

Specifically out pointers/output parameters.
<!-- .element: class="fragment" -->

`output` is the output of `uncompress` and `DecompressMessage` but is NEVER a return value.
<!-- .element: class="fragment" -->

<!-- This is maybe a bit mean -->
<!-- 
[//]: # (Vertical slide)

### Other notes

- `reinterpret_cast` is not UB here
- `const_cast` is though!!!!
- The correct usage of `DataRange` is `output.data<Bytef>()`
- `DataRange` inherits from `ConstDataRange`; data gets `const_cast`ed
- Both ranges only hold bytes anyway so `reinterpret_cast` is pointless

(maybe don't use MongoDB for user data...?)
-->

---

## C++ guidelines

As with most programming languages, outputs should be returned, not parameter.

To combat this MongoDB devs should have returned a view!

---

## Output Parameters

There are ways to make [output parameters better](https://www.foonathan.net/2016/10/output-parameter/#) but most are not perfect.

For example [std::outptr](https://en.cppreference.com/w/cpp/memory/out_ptr_t/out_ptr) is a very good way of interacting with C APIs.

<sub><sup>But would not have helped here</sub></sup>
<!-- .element: class="fragment small" -->

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

```C [1|2-4|5-14|6-7|8-12]
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
<!-- .element: class="r-fit" wants="compiles" -->


[//]: # (Vertical slide)

Ignoring the value of an out parameter might be valid but in C you'd normally signify this by accepting `NULL` as the input.

In this example we don't accept `NULL` so we expect the output to be used by the caller.
<!-- .element: class="fragment" -->


---

### Statically Checking output parameters

As it's normal in C we can do it in C++.

<sub>Also it's too commonly useful for a compiler warning</sub>
<!-- .element: class="fragment small" -->

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
    // bad (prefer nullptr)
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


---

# Possible fixes

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
    // create a new view to avoid confusion
    output = {output.data(), length};

    if (ret != Z_OK) {
        return Status{ErrorCodes::BadValue, "Compressed message was invalid or corrupted"};
    }

    counterHitDecompress(input.length(), output.length());
    // doesn't matter what `length` we use now
    return {output.length()};
}
```
<!-- .element: class="r-fit" -->

[//]: # (Vertical slide)

While we're here might as well fix the `DataRange` classes:

(remove UB `const_cast`ing everywhere)

```C++
#include <cstddef>
#include <utility>
#include <tuple>
#include <type_traits>
#include <optional>

// zlib stand-in
int uncompress(char*, size_t*, const char*, size_t );
constexpr int Z_OK = 0;

namespace mongo {

namespace stand_ins {
    enum struct Status {
        Good,
        NotGood,
        BadValue
    };
    using ErrorCodes = Status;

    template<typename T>
    struct StatusWith {
        Status status = Status::Good;
        std::optional<T> t;
        StatusWith(Status s) : status{s}, t{} {}
        StatusWith(Status s, [[maybe_unused]] auto _) : status{s}, t{} {}
        StatusWith(T&& type) : status{Status::Good}, t{type} {}
    };
}

template <typename T>
concept isByte = sizeof(T) == 1 && std::is_integral_v<T> && (!std::is_same_v<T, bool>);

template <typename T>
concept ByteLike = isByte<T>;

template <typename T>
concept ContiguousContainerOfByteLike = requires (T t){ t.data(); isByte<decltype(*(t.data()))>; };


template<bool is_const>
class AnyDataRange {
protected:
    
    template <typename T>
    using DataOp = decltype(std::declval<T>().data());
    template <typename T>
    using SizeOp = decltype(std::declval<T>().size());
    template <typename T>
    using ValueTypeOp = typename T::value_type;
    

    public:
    using byte_type = char;
    using held_type_p = std::conditional_t<is_const, const byte_type*, byte_type*>;

    // You can construct a AnyDataRange from any byte-like sequence. Byte-like means an
    // integral type with a size of one.
    //
    // begin and end should point to the first and one past last bytes in
    // the range you wish to view.
    //
    // debug_offset provides a way to indicate that the AnyDataRange is
    // located at an offset into some larger logical buffer. By setting it
    // to a non-zero value, you'll change the Status messages that are
    // returned on failure to be offset by the amount passed to this
    // constructor.
    AnyDataRange(ByteLike auto* begin, ByteLike auto* end, std::ptrdiff_t debug_offset = 0)
        : _begin(reinterpret_cast<held_type_p>(begin)),
          _end(reinterpret_cast<held_type_p>(end)),
          _debug_offset(debug_offset) {
        // invariant(end >= begin);
    }

    AnyDataRange() = default;

    // Constructing from nullptr, nullptr initializes an empty AnyDataRange.
    AnyDataRange(std::nullptr_t, std::nullptr_t, std::ptrdiff_t debug_offset = 0)
        : _begin(nullptr), _end(nullptr), _debug_offset(debug_offset) {}

    // You can also construct from a pointer to a byte-like type and a size.
    AnyDataRange(const ByteLike auto* begin, std::size_t length, std::ptrdiff_t debug_offset = 0)
        : _begin(reinterpret_cast<held_type_p>(begin)),
          _end(reinterpret_cast<held_type_p>(std::next(_begin, length))),
          _debug_offset(debug_offset)
    {
        static_assert(is_const, "Cannot construct non-const data range from const data");
    }

    AnyDataRange(ByteLike auto* begin, std::size_t length, std::ptrdiff_t debug_offset = 0)
    : _begin(reinterpret_cast<held_type_p>(begin)),
        _end(reinterpret_cast<held_type_p>(std::next(_begin, length))),
        _debug_offset(debug_offset) {}

    // AnyDataRange can also act as a view of a container of byte-like values, such as a
    // std::vector<uint8_t> or a std::array<char, size>. The requirements are that the
    // value_type of the container is byte-like and that the values be contiguous - the container
    // must have a data() function that returns a pointer to the front and a size() function
    // that returns the number of elements.
    AnyDataRange(const ContiguousContainerOfByteLike auto& container, std::ptrdiff_t debug_offset = 0)
        : AnyDataRange(container.data(), container.size(), debug_offset) {}

    // You can also construct from a C-style array, including string literals.
    template <size_t N>
    AnyDataRange(ByteLike auto (&arr)[N], std::ptrdiff_t debug_offset = 0)
        : AnyDataRange(arr, N, debug_offset) {}

    template <typename ByteLike = byte_type>
    auto* data() const noexcept {
        if constexpr (std::is_same_v<ByteLike, byte_type>) {
            return _begin; 
        } else {
            return reinterpret_cast<const ByteLike*>(_begin);
        }
    }

    template <typename ByteLike = byte_type>
    auto* data() noexcept {
        if constexpr (std::is_same_v<ByteLike, byte_type>) {
            return _begin; 
        } else {
            return reinterpret_cast<ByteLike*>(_begin);
        }
    }

    size_t length() const noexcept {
        // Assume silences a compiler warning
        //  Guarenteed to be the case because of 
        //   invariant(end >= begin)
        //  in constructor
        [[assume((_end - _begin) > 0)]];
        return static_cast<size_t>(_end - _begin);
    }

    bool empty() const noexcept {
        return length() == 0;
    }

    // template <typename T>
    // Status readIntoNoThrow(T* t, size_t offset = 0) const noexcept {
    //     if (offset > length()) {
    //         return makeOffsetStatus(offset);
    //     }

    //     return DataType::load(
    //         t, _begin + offset, length() - offset, nullptr, offset + _debug_offset);
    // }

    // template <typename T>
    // void readInto(T* t, size_t offset = 0) const {
    //     uassertStatusOK(readIntoNoThrow(t, offset));
    // }

    // template <typename T>
    // StatusWith<T> readNoThrow(std::size_t offset = 0) const noexcept {
    //     T t(DataType::defaultConstruct<T>());
    //     Status s = readIntoNoThrow(&t, offset);

    //     if (s.isOK()) {
    //         return StatusWith<T>(std::move(t));
    //     } else {
    //         return StatusWith<T>(std::move(s));
    //     }
    // }

    template <typename T>
    T read(std::size_t offset = 0) const {
        return uassertStatusOK(readNoThrow<T>(offset));
    }

    /**
     * Split this ConstDataRange into two parts at `splitPoint`.
     * May provide either a pointer within the range or an offset from the beginning.
     */
    template <typename T>
    auto split(const T& splitPoint) const {
        return doSplit<AnyDataRange<is_const>>(splitPoint);
    }

    /**
     * Create a smaller chunk of the original ConstDataRange.
     * May provide either a pointer within the range or an offset from the beginning.
     */
    template <typename T>
    auto slice(const T& splitPoint) const {
        return doSlice<AnyDataRange<is_const>>(splitPoint);
    }

    // template<typename Any, bool AnyBool>
    friend bool operator==(const AnyDataRange<is_const>& lhs, const AnyDataRange<is_const>& rhs) {
        return std::tie(lhs._begin, lhs._end) == std::tie(rhs._begin, rhs._end);
    }

    friend bool operator!=(const AnyDataRange<is_const>& lhs, const AnyDataRange<is_const>& rhs) {
        return !(lhs == rhs);
    }

    std::ptrdiff_t debug_offset() const {
        return _debug_offset;
    }

    template <typename H>
    friend H AbslHashValue(H h, const AnyDataRange& range) {
        return H::combine_contiguous(std::move(h), range.data(), range.length());
    }

protected:
    // Shared implementation of split() logic between DataRange and ConstDataRange.
    template <typename RangeT, typename ByteLike, std::enable_if_t<isByte<ByteLike>, int> = 0>
    std::pair<RangeT, RangeT> doSplit(const ByteLike* splitPoint) const {
    }

    template <typename RangeT>
    auto doSplit(std::size_t splitPoint) const {
        return doSplit<RangeT>(data() + splitPoint);
    }

    // Convenience wrapper to just grab the first half of a split.
    template <typename RangeT, typename T>
    RangeT doSlice(const T& splitPoint) const {
        auto parts = doSplit<RangeT>(splitPoint);
        return parts.first;
    }

protected:
    held_type_p _begin = nullptr;
    held_type_p _end = nullptr;
    std::ptrdiff_t _debug_offset = 0;

    Status makeOffsetStatus(size_t offset) const;
};

using ConstDataRange = AnyDataRange<true>;
using DataRange = AnyDataRange<false>;

// Bytef stand in
using Bytef = char;

StatusWith<std::size_t> decompressData(ConstDataRange input,
                                       DataRange output) {
    std::size_t length = output.length();
    int ret = ::uncompress(
                    output.data<Bytef>(),
                    &length,
                    input.data<Bytef>(),
                    input.length()
        );
    output = {output.data(), length};

    if (ret != Z_OK) {
        return Status{ErrorCodes::BadValue, "Compressed message was invalid or corrupted"};
    }

    // counterHitDecompress(input.length(), output.length());
    return {output.length()};
}

}
```
<!-- .element: class="r-fit" wants="compiles" -->


