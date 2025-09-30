# Make it Till you Fake It

Multiple Methods to Mock

---

## What is mocking?

---

### Python: Mocking Functions

```py
def app_code():
    print("hello")

from unittest.mock import Mock
app_code = Mock() # set to a mock object

# call the mock object (in test)
app_code()
# do assertions on the mock object
app_code.assert_called_once()
```
<!-- .element: class="unknown" wants="runs" -->

[//]: # (Vertical slide)

Classes can be done similarly:
```py
class AppCode:
    def help(self):
        print("help")
from unittest.mock import Mock
app = Mock()
# in unit test
app.help() # each name lookup returns a mock object
app.help.assert_called_once() # do assertions on the mock object
```
<!-- .element: class="unknown" wants="runs" -->

---

## Python for 3rd Party

If building tests with dependency, third parties can be mocked as shown previously.

[//]: # (Vertical slide)

You can also mock out modules by using `sys.modules`, even if we do not have the module available:

```py
import sys
from unittest.mock import Mock
# Acts as an import of `os`, but os is a mock object not a real one
sys.modules["os"] = Mock() 

from os import sep

# sep is also a mock object
print(f"{sep.__doc__=}")
```
<!-- .element: class="unknown" wants="compiles" -->

[//]: # (Vertical slide)

```py
import sys
from unittest.mock import Mock
# Import something third party
sys.modules["something"] = Mock()
# import is cached, making it available (everywhere)
import something
# mock object is called
something.help()
# can do assertions on the mock object
something.help.assert_called_once()
# To undo: pop it
sys.modules.pop("something")
```
<!-- .element: class="runs" wants="runs" -->

---

## Python for complete modules

You can also use a local version of the module instead of the real one.

[//]: # (Vertical slide)

Mocking a third party dependency by giving it a local version (mocked) instead:
```py
import sys
# With 3rd party module **NOT** in build
# Append to path:
#   (where packages are looked up from)
sys.path.append("/home/foo")

# Now import redirects to /home/foo folder
import foo
```

---

## C++ Mocking:

----

### SIMD JSON

[//]: # (Vertical slide)

In C++ you cannot alter what a function does at runtime.
You can however store a function pointer in a class and reassign that function pointer to another function.
SIMDJson does this in [simdjson.cpp](https://github.com/simdjson/simdjson/blob/master/src/simdjson.cpp);

[//]: # (Vertical slide)

```C++
struct CallableHolder {
	using func_t = void(*)(int);
	func_t&       get_func()       { return m_func; }
	const func_t& get_func() const { return m_func; }
	
	func_t m_func = nullptr;
};

CallableHolder& get_callable_holder() {
	static CallableHolder callable_holder_singleton{};
	return callable_holder_singleton;
}

int main() {
	get_callable_holder().get_func() = +[](int){};
	get_callable_holder().get_func()(5);
}
```
<!-- .element: class="r-stretch" wants="compiles" -->

[//]: # (Vertical slide)

This strategy/registry pattern hybrid allows for changing the app code function at runtime, and can therefore be mocked easily.
```C++
// With some mocking magic
get_callable_holder().get_func() = mocks.mock_func;
ASSERT_EQ(mocks.called.mock_func, 1U);
```

---

### GMock + OOP

If your app code uses OOP, you can mock everything that was interfaced.

[//]: # (Vertical slide)

```C++
struct Interface { virtual int foo() = 0; };
struct Impl : Interface {
	int foo() override { return 1; }
};

int use_Impl(Interface& interface) {
	return interface.foo();
}
int main() { return Impl{}.foo(); }
```
<!-- .element: class="r-stretch" wants="compiles" -->

<sub><sup>Can be mocked && tested with:</sup></sup>

[//]: # (Vertical slide)

```C++
#include <gmock/gmock.h>

struct MockImpl : Interface {
	MOCK_METHOD(int, foo, (), (override));
};

TEST(SuiteName, TestName) {
	MockImpl mock{};
	EXPECT_CALL(mock, foo()).Times(1);
	use_impl(mock);
}
```
---

### GMock + Templates

OOP often has a performance overhead, is often implemented with heavy heap usage and often a single function is better.

You can use templates to mock single functions, classes and concepts.

[//]: # (Vertical slide)

```C++
template<typename T = Impl>
int use_impl(T& impl) { return impl.foo(); }

#include <gmock/gmock.h>

struct MockImpl { MOCK_METHOD(int, foo, ()); };

TEST(SuiteName, TestName) {
	MockImpl mock{};
	EXPECT_CALL(mock, foo()).Times(1);
	use_impl(mock);
}
```
---

### Mocking Third-Party libs

To mock a third party package you could:

[//]: # (Vertical slide)

1. Wrap it in a class
2. Have that class be interfaced
3. Create a mock object for that interface
4. Have all app code only use the interface
<sub><sup>(bridge)</sub></sup>

[//]: # (Vertical slide)
or

1. Wrap it in a class (no interface)
2. Create a mock object for that concept
3. Have all app code always template that concept

[//]: # (Vertical slide)
or

1. Recreate the entire lib's header files
2. Include that header file path in your test build

[//]: # (Vertical slide)

|   | pros    |  cons   |
| - | ---- | ---- |
| Bridge | OOP | OOP, overhead, some code changes |
| Templates | No overhead | Less compile time checks (pre concepts), post concepts: higher build times, some code changes |
| Headers | No overhead, No code changes, shorter build times, smaller test exes | A bit of a faff, Requires a fair amount of language knowledge, Changes in build system |
<!-- .element: class="r-fit-text r-frame" -->
[//]: # (adding fragment here causes the whole table to pop in rather than one column per)
[//]: # (A pr exists added but didn't do markdown so looks unlikely)

---

I have rewritten the headers for CppUnit for the tests to execute using the GTest runtime: [CppUnit2Gtest](https://github.com/OlekRaymond/CppUnit2Gtest).

Thus all CppUnit test code remains as is, new tests can be written in gtest style (incremental adoption) and all tests output as if they were written as gtest.

[//]: # (Vertical slide)

[Reasoning/Advertisement](./CppUnit2Gtest.html)

[//]: # (Vertical slide)

No code changes are required:

[All CppUnit examples compile as expected](https://github.com/OlekRaymond/CppUnit2Gtest/tree/main/tests/examples)

Proof/PR to [LibreOffice](https://www.libreoffice.org/) is WIP

[//]: # (Vertical slide)

CppUnit and gtest macros can be used interchangeably:

[See Migration guide](https://github.com/OlekRaymond/CppUnit2Gtest/blob/main/tests/examples/Migrating.cpp)
for more info.

[//]: # (Vertical slide)

Well Tested

- 100% coverage
- 100% mutation test score
- Compiles with `Wall` and `Wextra`
- Address and UB sanitized

[//]: # (Vertical slide)

Deprecated CppUnit macros are respected
```C++
#define CPPUNIT_TEST_SUITE_REGISTRATION(Class_name) CPPUNIT_TEST_SUITE_NAMED_REGISTRATION(Class_name, #Class_name)

#define CPPUNIT_TEST_SUITE_NAMED_REGISTRATION(Class_name, suite_additional_name ) namespace{ \
    static const size_t Cpp2Gtest_UNIQUE_NAME(unused_) = \
    ::CppUnit::to::gtest::InternalRegisterTests<Class_name>(#Class_name, __LINE__, suite_additional_name); \
}
```
[//]: # (Vertical slide)

Asserts are name forwarded to gtest equivalents to give more information

```C++
#define CPPUNIT_ASSERT(condition)                                    ASSERT_TRUE(condition)
```

[//]: # (Vertical slide)

Features not implemented are ignored (no code change required to compile):
```C++
// If we want CPPUNIT_TEST_SUITE_PROPERTY we have to call `::testing::Test::RecordProperty`
//  but we have to do it after SetUpTestSuite and before TearDownTestSuite
//  the macro is called between CPPUNIT_TEST_SUITE and CPPUNIT_TEST_SUITE_END (needs proof)
//   so we'd need some state on the class and set it in the `GetAllTests_` function

// Do nothing for now
#define CPPUNIT_TEST_SUITE_PROPERTY( unused_1, unused_2 )
```

