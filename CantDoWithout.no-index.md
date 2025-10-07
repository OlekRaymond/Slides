
# Code I can't live without

---

Getting the class name:
```C++
#if __has_include(<cxxabi.h>)
#   include <cxxabi.h>
#   define Ray_Demanglable
#endif
#include <typeinfo>
#include <string>

template<typename T>
[[nodiscard]] auto GetTypeName() {
    
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
<!-- .element: class="r-stretch" wants="compiles no_main" -->

---

CRTP logging class:
```C++

template<typename Derived>
struct Logger : Derived {
private:
    auto GetDerivedName() {
        return GetTypeName<Derived>();
    }

    Logger() { std::cout << GetDerivedName() << "()\n"; }
    Logger(Logger&&) { auto name = GetDerivedName(); std::cout << name << "(name&&)\n"; }
    Logger(const Logger&) { auto name = GetDerivedName(); std::cout << name << "(const " << name << "&)\n"; }
    Logger& operator=(Logger&&) { auto name = GetDerivedName(); std::cout << name << "=" << name "&&\n"; }
    Logger& operator=(const Logger&) { auto name = GetDerivedName(); std::cout << name << "= const" << name "&\n"; }
    ~Logger() { std::cout << "~" << GetDerivedName(); << "()\n"; }
};
```
<!-- .element: class="r-stretch" wants="compiles no-main append" -->

---

Lippincott error handling:
```C++
#include <iostream>
#include <exception>

void HandleError() {
    const auto print_std = {}(const auto& exception) {
        return (std::cout << "Error: " << GetTypeName(exception) << ":" << e.what() << "\n");
    };
    try {
        throw;
    // Your custom exceptions
    } catch (const std::nested_exception& e) {
        print_std(e);
        try { std::rethrow_if_nested(e) } catch (...) { std::cout << "From: "; HandleError(); }
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
<!-- .element: wants="compiles no-main append" id="lip" -->

---

Stack Traces:
```C++
#if __cpp_lib_stacktrace >= 202011L
#   include <stacktrace>
inline auto GetStackTrace() { return std::stacktrace::current(); }
#else
#   include <boost/stacktrace.hpp>
inline auto GetStackTrace() { return boost::stacktrace::stacktrace(); }
#endif
```

<!-- This and the following need C++23 to compile, TODO: add flags section to wants -->

[//]: # (Vertical slide)

Stack Traces on exit:
```C++
# include <iostream>

int main() { 
    std::set_terminate([](){ std::cout << GetStackTrace() << "\n"; });
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
    using std::string_literals
    
    CustomException(const std::string& what)
      : std::logic_error("CustomException: "s + what + " From trace: "s + GetStackTrace())
    { }
    // Explicit const char* is deleted, what is not overridden

    CustomException(const CustomException&) = default;
    CustomException& operator=(const CustomException&) = default;
};
```

---

(Some) warnings as errors:
```C++
// -Werror=shadow
//   requiring shadowing reveals a lack of imagination
auto foo() { float h{1}; float h{2}; return h; }
// -Werror=infinite-recursion
int bar() { return bar(); } // Always a crash
```
<!-- .element: wants="compiles" -->

[//]: # (Vertical slide)

Get feedback before ASAN runs:
```C++
#include <stdlib.h>
// -Werror=return-local-addr
auto& foo() { float h{1.0}; return h; } // UB
// -Werror=null-dereference
int baz() { int* i_p = nullptr; return *i_p; } // Always a crash
// -Werror=mismatched-dealloc
int foo() { auto p = new int[10]; free(p);     return 1; } // Triggers ASAN
int foo2() { auto p = new int[10]; delete p;   return 1; } // Triggers ASAN
int foo3() { auto p = new int[10]; delete[] p; return 1; } // Good
```
<!-- .element: wants="compiles" -->

