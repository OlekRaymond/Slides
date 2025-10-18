
# CppUnit2Gtest

A header only library to remove legacy dependencies

---

## A blast to the past:

Pre C++98, we didn't have a standard so each "standard library" was very different, so portable libraries often wrote everything from scratch.

This is less than ideal. In ~~modern~~ not old C++ we can simply overload the stream operator to print something to screen.

[//]: # (Vertical slide)

### Enter Junit:

Junit is a Java testing library, it's pretty good!

- Test suites written as single class.
- Tests declared easily with `@test`.
- Optionally outputs a custom, readable XML format.
- Asserts are easy to write

[//]: # (Vertical slide)

### Enter CppUnit:

CppUnit attempts to hop on the bandwagon

and lands, <!-- .element: class="fragment" -->

face first, <!-- .element: class="fragment" -->

in the dirt. <!-- .element: class="fragment" -->

[//]: # (Vertical slide)

Early Junit made a decision to have the message first, then the objects to assert. (i.e. optional argument first).

Junit has since removed this in favour of the message as the last parameter.
<!-- .element: class="fragment" -->

CppUnit has not made such a change.
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

Junit created a great XML format that could be parsed by other tools, allowing for easy visualisation.

Many other testing frameworks saw these benefits and decided to also produce output in the same format to make use said tools. 
<!-- .element: class="fragment" -->

CppUnit used a different XML schema so it's not compatible. 
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

Java has reflection so there is always some method of printing some information about an object.

Pre C++98 there was no standard way to print an object so CppUnit wrote a custom method.
<!-- .element: class="fragment" -->

They since added a custom stream to maintain backwards compatibility.
<!-- .element: class="fragment" -->

If you add neither the tests fail to compile.
<!-- .element: class="fragment" -->

If add one for the tests you get a warning in release.
<!-- .element: class="fragment" -->

<sub><sup>You have warnings as errors on so it still doesn't compile</sup></sub>
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

In Junit each test is surrounded by a `try`-`catch`-all. So if an exception is thrown from within a test it is caught and added to the test results.

In CppUnit it is not.
<!-- .element: class="fragment" -->

Each test is surrounded by a "protector" class which the user writes and does all the catching.
<!-- .element: class="fragment" -->

If an exception is not caught the program exits and no test results are given.
<!-- .element: class="fragment" -->

---

## Fixes:

[//]: # (Vertical slide)

CppUnit allows you to fix lots of these because it's so extendable, 

However:
- Git prints in colour <!-- .element: class="fragment" -->
- Python interpreter prints in colour <!-- .element: class="fragment" -->
- gcc prints in colour <!-- .element: class="fragment" -->
- Junit prints in colour <!-- .element: class="fragment" -->
- gtest prints in colour <!-- .element: class="fragment" -->
- doctest prints in colour <!-- .element: class="fragment" -->
- Python's (built in) unit test print in colour <!-- .element: class="fragment" -->

[//]: # (Vertical slide)

Why do I have to write code for CppUnit to print in colour?
<!-- .element: class="fragment" -->

Why do I have to write a custom outputer?
<!-- .element: class="fragment" -->

Why do I have know all possible thrown exceptions?
<!-- .element: class="fragment" -->

Why do I have to print all the data from my classes?
<!-- .element: class="fragment" -->

Why can't testing be easy?
<!-- .element: class="fragment" -->

---

## What is it?

CppUnit2Gtest is a single header file that uses macro magic to register tests written for CppUnit to work with gtest.
<!-- .element: class="fragment" -->

There are no requirements for CppUnit tests to be rewritten. 
<!-- .element: class="fragment" -->

New tests can be written in gtest or CppUnit styles with no issues.
<!-- .element: class="fragment" -->

The only code change required is in the main (because CppUnit makes you write a custom main)
<!-- .element: class="fragment" -->

---

## Why?

Testing should be easy,  <!-- .element: class="fragment" -->

testing in CppUnit was hard,  <!-- .element: class="fragment" -->

I made it easy  <!-- .element: class="fragment" -->

