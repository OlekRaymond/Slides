
# Clang Tidy good!

---

## What checks do I turn on?

[//]: # (Vertical slide)

Codon has these:
- clang-diagnostic-*
- clang-analyzer-*
- cppcoreguidelines-*
- modernize-*
- bugprone-*
- concurrency-*
- performance-*
- portability-*

[//]: # (Vertical slide)

DuckDB has these:
- clang-diagnostic-*
- bugprone-*
- performance-*
- google-explicit-constructor
- google-build-using-namespace
- google-runtime-int
- misc-definitions-in-headers
- modernize-use-nullptr
- modernize-use-override
- readability-braces-around-statements
- readability-identifier-naming
- hicpp-exception-baseclass
- misc-throw-by-value-catch-by-reference
- google-global-names-in-headers
- llvm-header-guard
- misc-definitions-in-headers
- modernize-use-emplace
- modernize-use-bool-literals
- readability-container-size-empty
- cppcoreguidelines-pro-type-cstyle-cast
- cppcoreguidelines-pro-type-const-cast
- cppcoreguidelines-avoid-non-const-global-variables
- cppcoreguidelines-interfaces-global-init
- cppcoreguidelines-slicing
- cppcoreguidelines-rvalue-reference-param-not-moved
- cppcoreguidelines-virtual-class-destructor

[//]: # (Vertical slide)

Jason Turner has these turned off (and all others on):
- abseil-*,
- altera-*,
- android-*,
- fuchsia-*,
- google-*,
- llvm*,
- modernize-use-trailing-return-type,
- zircon-*,
- readability-else-after-return,
- readability-static-accessed-through-instance,
- readability-avoid-const-params-in-decls,
- cppcoreguidelines-non-private-member-variables-in-classes,
- misc-non-private-member-variables-in-classes,
- misc-no-recursion,
- misc-use-anonymous-namespace,
- misc-use-internal-linkage
