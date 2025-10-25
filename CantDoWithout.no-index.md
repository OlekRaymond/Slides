
# Code I can't live without

---

### Getting the class name:
```C++
#if __has_include(<cxxabi.h>)
#   include <cxxabi.h>
#   define Ray_Demanglable
#endif
#include <typeinfo>
#include <string>
#include <iostream>

template<typename T>
[[nodiscard]] std::string GetTypeName() {
    
    const auto name = typeid(T).name(); // remove const ref optional
#if defined(Ray_Demanglable)
    size_t length = 0;
    int status = 0;
    const auto demangled = abi::__cxa_demangle
        (
            name, // remove const ref optional
            nullptr,
            &length,
            &status
        );
    if (status == 0 && length != 0 && demangled != nullptr) {
        std::string result{demangled, length};
        free(demangled);
        return result;
    }
    else
#endif
        return std::string{name};
}
```
<!-- .element: class="r-stretch" wants="compiles no_main" id="className" -->

---

### CRTP logging class:
```C++
template<typename Derived>
struct LifeTimeLogger {
private:
    auto GetDerivedName() {
        return GetTypeName<Derived>();
    }
public:
    LifeTimeLogger() { std::cout << GetDerivedName() << "()\n"; }
    LifeTimeLogger(LifeTimeLogger&&) { auto name = GetDerivedName(); std::cout << name << "(name&&)\n"; }
    LifeTimeLogger(const LifeTimeLogger&) { auto name = GetDerivedName(); std::cout << name << "(const " << name << "&)\n"; }
    LifeTimeLogger& operator=(LifeTimeLogger&&) { auto name = GetDerivedName();std::cout << name << "=" << name << "&&\n"; }
    LifeTimeLogger& operator=(const LifeTimeLogger&) { auto name = GetDerivedName(); std::cout << name << "= const" << name << "&\n"; }
    ~LifeTimeLogger() { std::cout << "~" << GetDerivedName() << "()\n"; }
};
```
<!-- .element: class="r-stretch" wants="compiles no-main append" id=logger" -->

[//]: # (Vertical slide)

```C++
struct L : LifeTimeLogger<L> { int i = 0; };
int main() {
    L l{};
    return l.i;
}
```
<!-- .element: wants="runs append" -->


---

Lippincott error handling:
```C++
#include <iostream>
#include <exception>

void HandleError() {
    const auto print_std = [](const auto& e) {
        std::cout << "Error: " << GetTypeName<decltype(e)> () << ":" << e.what() << "\n";
    };
    try {
        throw;
    // Your custom exceptions
    } catch (const std::nested_exception& e) {
        // print_std(e);
        try { std::rethrow_if_nested(e); } catch (...) { std::cout << "From: "; HandleError(); }
    } catch (const std::logic_error& e) {
        print_std(e);
    } catch (const std::runtime_error& e) {
        print_std(e);
    } catch (const std::exception& e) {
        print_std(e);
    } catch (...) {
        std::cout << "Error: Unknown exception thrown\n";
    }
}
void Usage() {
    try {
        const auto something_that_may_throw = [](){};
        something_that_may_throw();
    } catch(...) {
        HandleError();
    }
}
```
<!-- .element: class="r-fit" wants="compiles no-main append className" id="lip" -->

---

Stack Traces:
```C++
#if __cpp_lib_stacktrace >= 202011L
#   include <stacktrace>
    inline auto GetStackTrace() {
        return std::stacktrace::current();
    }
#else
#   include <boost/stacktrace.hpp>
    inline auto GetStackTrace() {
        return boost::stacktrace::stacktrace();
    }
#endif
```

<!-- This and the following need C++23 to compile, TODO: add flags section to wants -->

[//]: # (Vertical slide)

Stack Traces on exit:
```C++
# include <iostream>

int main() { 
    std::set_terminate(
        [](){ std::cout << GetStackTrace() << "\n"; }
    );
}
```

[//]: # (Vertical slide)

Credit to [boost](https://github.com/boostorg/stacktrace/blob/develop/example/terminate_handler.cpp) for the idea.

Crashes/exit signals don't work with this though.

Boost provides something to dump the trace on signal exit, but it is UB (i.e. fine in a test app)

ASAN tends to give a nice stacktrace and should be on for tests anyway.

[//]: # (Vertical slide)

Stack traces on exceptions:
```C++
struct CustomException : std::logic_error {
    using std::string_literals;
    
    CustomException(const std::string& what)
      : std::logic_error(
        "CustomException: "s + what + " From trace: "s + GetStackTrace()
    ) { }
    
    CustomException(const CustomException&) = default;
    CustomException& operator=(const CustomException&) = default;
};
```


---

(Some) warnings as errors:
```C++
// -Werror=shadow
//   requiring shadowing reveals a lack of imagination
auto foo() { float h{1}; { float h{2}; return h; } }

// -Werror=infinite-recursion
int crash() { return crash(); }

// -Werror=return-type
//  no return statement in function returning non-void
int return_stack() { };
```
<!-- .element: wants="compiles" -->

[//]: # (Vertical slide)

Get feedback before ASAN runs:
```C++
#include <stdlib.h>

// -Werror=return-local-addr
auto& UB() { float h{1.0}; return h; }

// -Werror=null-dereference
int crash() { int* i_p = nullptr; return *i_p; }

// -Werror=mismatched-dealloc
int ASAN() { int* p = new int[10]; free(p);    return 1; }
int ASAN2() { int* p = new int[10]; delete p;  return 1; }
int good() { int* p = new int[10]; delete[] p; return 1; }
```
<!-- .element: wants="compiles" -->

[//]: # (Vertical slide)

For ease of coping:
```
-Werror=shadow
-Werror=infinite-recursion
-Werror=return-type
-Werror=return-local-addr
-Werror=null-dereference
-Werror=mismatched-dealloc
```

---

### CRTP Name forwarding

[//]: # (Vertical slide)

We use CRTP all the time: [strong typing libs](github.com/rollbear/strong_type), [unit libs](), [lifetime logging code^](#crtp-logging-class), [serialisation code]()

---

# Things I like but aren't essential

---

Reduction of soft contracts (and documentation) through API design

[//]: # (Vertical slide)

```C++
#include <optional>
#include <cstddef>
#include <type_traits>

template<typename V>
struct Optional {
    constexpr Optional(V&& value) : value_(value) {}

    constexpr auto isValid() const { return ValidType<true>(*this); }
    constexpr auto isValid() { return ValidType<false>(*this); }

private:
    std::optional<V> value_;
    template<bool is_const>
    struct ValidType {
        using UnderlyingType = typename std::conditional<is_const, const std::optional<V>, std::optional<V>>::type;
        constexpr V get() {
            return value_.get();
        }
        constexpr const V* operator->() const { return value_.value(); }
        constexpr V* operator->() { return value_.value(); }
        constexpr const V& operator*() const & { return value_.value(); }
        constexpr V& operator*() & { return value_.value(); }
        constexpr const V&& operator*() const && { return value_.value(); }
        constexpr V&& operator*() && { return value_.value(); }
        constexpr operator bool() { return value_.has_value(); }


    private:
        friend Optional;
        template<typename O>
        constexpr ValidType(O& o) : value_{o.value_} { /*static_assert(O is Optional)*/ }
        UnderlyingType& value_;
        ValidType() = delete;
        ValidType(ValidType&&) = delete;
        ValidType(const ValidType&) = delete;
    };
};
```
<!-- .element: class="r-fit" wants="compiles no-main" -->

[//]: # (Vertical slide)

```C++
int main() {
    Optional<int> optional{0};
    // auto compiler_error = optional.get();

    // Must be auto (anonymous type)
    if (auto valid = optional.isValid(); valid) {
        return *valid;
    }
}
```
<!-- .element: wants="runs append" -->

---

Soft contracts can also be reduced using `constexpr` and `static_asserts`
```C++
#include <string_view>

constexpr bool ContainsUnderscores(const std::string_view suite_name) {
    return suite_name.find("_") != std::string_view::npos;
}

#define SomeMacro(item)                                     \
    static_assert(!ContainsUnderscores(#item),              \
        "item names are not allowed to contain underscores" \
    );                                                      \
    NormalMacro...
```

---

# Things I have yet to use but kinda fit
## (Reflection adjacent)

---

```C++
#include <string_view>

constexpr bool is_msvc() noexcept {
    return
#ifdef _MSC_BUILD
    true
#else 
    false
#endif
    ;
}

constexpr bool is_structor_impl(std::string_view name) {
    // "A::A()" format is a constructor
    // "A::~A()" format is a destructor
    // "int A::b()" format is a method
    // operator bool seems print with a return type
    // everything else should have a space
    using namespace std::string_view_literals;
    constexpr auto member_call_windows = "__thiscall "sv;

    if (is_msvc()) {
        if (name.find(member_call_windows) == name.npos ){
            return false;
        }
        name.remove_prefix(member_call_windows.size());
        if (name.find("(void)") == name.npos ){
            return false;
        }
    }

    const auto space = name.find(' ');
    if (space != name.npos) { return false; }
    return true;
}

#ifndef _MSC_BUILD
#   define is_structor() is_structor_impl(__PRETTY_FUNCTION__)
#else 
#   define is_structor() is_structor_impl(__FUNCSIG__)
#endif
```
<!-- .element: class="r-fit" wants="compiles no-main" -->

[//]: # (Vertical slide)

Usage:

```C++
struct A {
    A() {
        static_assert(is_structor());
    }
    int b() {
        static_assert(!is_structor());
        return 1;
    }
    operator bool() {
        static_assert(!is_structor());
        return false;
    }
    ~A() { static_assert(is_structor()); }
};

int c = A{}.b();
bool b = A{};
```
<!-- .element: class="r-fit" wants="compiles no-main append" -->

---



