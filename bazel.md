
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
- Change a private `.hpp` file that is never used, nothing happens
- Add a comment to a `.cpp` file, the hash of the `.obj` doesn't change
- Change an inline function (in a `.hpp` file) that is never used the `.lib` hash doesn't change
- If nothing being tested changes, the tests aren't run

[//]: # (Vertical slide)

### So in python:

1. Each file contributes to a package
2. Each package forms a library/`__pycache__`
3. Each library can be used by a executable

[//]: # (Vertical slide)

So if I:
- Change a `.py` file, the library is recreated
- Change a `.pyi` file, nothing changes as it doesn't contribute to byte code
- Change a test file, the test is recreated and is reran
- Add docs/comments, the library is recreated*

[//]: # (Vertical slide)

Compiler arguments are stored as a file so if they change everything is recompiled.

Python allows you to get the source code of a file so comments are maintained. [You can control this though](https://bazel.build/reference/be/python#py_library_args) with `omit-source`

---

## Real world example:

[//]: # (Vertical slide)

The CI for a compiler might look like:
1. Build compiler libraries (modules that make up the code)
2. Run unit tests on these libraries
3. Build the compiler executable
4. Run compiler exe on data to create byte-code
5. Test created byte-code

[//]: # (Vertical slide)

So:
- If the libraries haven't changed we don't need to re compile them
- If the code we are testing hasn't changed there's no need to run the code
- If the compiler exe hasn't changed there's no need to test it
- If the byte-code hasn't changed there's no need to run it

[//]: # (Vertical slide)

### Smoke testing

Tests can be given a size, `size="small"`, which implies their timeout.

This is most useful when doing unit testing before a commit, to only run the small, short tests: `--test_size_filters="small"`

Alternatively you can use a tag `tag="smoke"` and `--test_tag_filters="smoke"` (then `"-smoke"` to avoid running them with "real" tests)

---

## Package management:

Packages are got from [the bazel central registry](registry.bazel.build/)

via the `bazel_dep(` function in from within a `MODULE.bazel` file

e.g. `bazel_dep(name = "googletest", version = "1.17.0")`

[//]: # (Vertical slide)

### When packages go wrong:

You not like a package version:
- All packages can be overridden with:
    + git
    + a local copy (via path or archive)

e.g if [libgit2](github.com/libgit2/libgit2) creates a warning in user code, you can specify a fork instead of the original to avoid the warning.

This doesn't change anything else in the build files!

---

## Live coding(?):
- Simple single file example
- Multiple file example
- Wrap CMake example
- Wrap make example
- Get packages from bazel central registry
- Tagging

---

