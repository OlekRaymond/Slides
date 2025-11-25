
# Bazel Good
Not CMake, better(?)

---

## Built in package manager

Bazel has a built in package manger, if building with CMake you would otherwise need something like CPM (CMake package manager) or Conan (the frogarian)

---

## Graph theory

A directed acyclic graph (DAG) is:
- a graph
- edges only have one direction
- cannot loop

In Bazel each node is a file, each edge is a operation.

---

## Only build what you need

Bazel will only build packages that you rely on, anything unused is not seen.

As bazel builds this DAG, it easily knows what you do and don't need

---

## Only build what changes

When a file is changed we go up the DAG.

If an operation's (edge's) result (node) is identical to the last, it won't do the remaining steps.

i.e. It will only redo an operation if an input hash has changed.

[//]: # (Vertical slide)

### So in C++

1. Each file is compiled into an object file (.obj)
2. Object files are compiled into a static lib (.lib)
3. Static lib are linked into an executable (.exe)

[//]: # (Vertical slide)

So if I:
- change a private .hpp file that is never used, nothing happens
- add a comment to a .cpp file, the hash of the .obj doesn't change
- change an inline function (in a .hpp file) that is never used the .lib hash doesn't change
- if nothing being tested changes, the tests aren't run

[//]: # (Vertical slide)


### So in python:


<!-- C:\Users\olekr\Documents\Work\Experiment\BUILD -->

---

### Compilation tests
- Build compiler
- Run compiler
- Test compiled byte-code
- 


---

## Deps not in bazel

- Wrap CMake example
- Wrap make example




---