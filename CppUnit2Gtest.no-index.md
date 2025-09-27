
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

Junit has since removed this in favour of the message being at the end.
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

If you add neither the code fails to compile.
<!-- .element: class="fragment" -->

---

## What is it?

Converts tests written for CppUnit to be runnable with a Gtest.

---

## Why?

Testing should be easy