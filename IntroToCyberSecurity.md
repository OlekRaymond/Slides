# Intro to cyber security

---

## A memory error is a security vulnerability.

[//]: # (Vertical slide)

This includes:
- Accessing an address which has not been allocated
<!-- .element: class="fragment" -->
- Accessing an address which has been deallocated
<!-- .element: class="fragment" -->
- Reading data which has not been set (usually)
<!-- .element: class="fragment" -->

---

To avoid these we have sanitizers


[//]: # (Vertical slide)

A sanitizer will check that X thing has not happened, if it has it will trigger a program exit (abort)

- Address sanitizer checks that the address of accessed memory
<!-- .element: class="fragment" -->
- Memory sanitizer checks that any accessed memory has been set
<!-- .element: class="fragment" -->

---

A denial of service is obviously a security vulnerability.

So in a web service any exit is a security vulnerability.
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

```python
from fastapi import FastAPI, Request
app = FastAPI()

@app.post("/login")
def login(username: str, payload: dict):
    status = payload.get("status")
    user_type = username
    
    if status == "kill":
        sys.exit(1)
        
    if user_type == "admin":
        raise ValueError("No admins allowed")
        
    return {"message": "ok"}
```
<!-- .element: class="r-stretch" -->

[//]: # (Vertical slide)

Or the famous:
```rust
let (features, _) = 
    features.append_with_names(&self.config.feature_names)
    .unwrap();
```

[//]: # (Vertical slide)

Exits are not desirable in embedded contexts.

---

Given:
> A program exit is security vulnerability

We can say:
<!-- .element: class="fragment" -->
> To prove a program is secure, we must prove that it will never exit
<!-- .element: class="fragment" -->

---

As that's impossible

We, traditionally, test with many inputs to assert that all inputs satisfies some property.
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

This is known as property testing.

Testing exclusively for the property "doesn't crash" is called fuzz testing
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

[Fuzz testing output here](https://github.com/OlekRaymond/CommandManagerTest/actions/runs/42858775389/job/129978917876#step:7:1)

[//]: # (Vertical slide)

```
#2	INITED ft: 6 corp: 1/1b exec/s: 0 rss: 28Mb
#713	NEW    ft: 7 corp: 2/12b lim: 11 exec/s: 0 rss: 28Mb L: 11/11 MS: 1 InsertRepeatedBytes-
#2138	NEW    ft: 8 corp: 3/35b lim: 25 exec/s: 0 rss: 28Mb L: 23/23 MS: 5 CopyPart-InsertByte-ShuffleBytes-ChangeBinInt-InsertRepeatedBytes-
#2495	REDUCE ft: 8 corp: 3/34b lim: 25 exec/s: 0 rss: 28Mb L: 22/22 MS: 2 ChangeByte-EraseBytes-
#6812	REDUCE ft: 14 corp: 4/57b lim: 63 exec/s: 0 rss: 28Mb L: 23/23 MS: 2 ChangeByte-InsertByte-
#6849	REDUCE ft: 14 corp: 4/55b lim: 63 exec/s: 0 rss: 28Mb L: 21/22 MS: 2 ChangeBinInt-EraseBytes-
#6906	REDUCE ft: 14 corp: 4/47b lim: 63 exec/s: 0 rss: 28Mb L: 13/22 MS: 2 ChangeByte-EraseBytes-
#6982	REDUCE ft: 14 corp: 4/46b lim: 63 exec/s: 0 rss: 28Mb L: 12/22 MS: 1 EraseBytes-
```
<!-- .element: class="r-stretch" -->

---

Instead of dynamically going down the callstack from an input.

We can statically go up from a possible issue, finding any inputs that might cause it
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

In this case we can find any call to exit, see what calls it and create constraints for an input that would trigger the exit.

This is called backward symbolic execution.
<!-- .element: class="fragment" -->

[//]: # (Vertical slide)

[Live demo](https://godbolt.org/#z:OYLghAFBqd5TKALEBjA9gEwKYFFMCWALugE4A0BIEAZgQDbYB2AhgLbYgDkAjF%2BTXRMiAZVQtGIHgBYBQogFUAztgAKAD24AGfgCsp5eiyagADgE8iSIeRWNURAkOrNMAYXT0ArmyYhZrgAyBEzYAHI%2BAEbYpFJaAJzkpuhKxE5MHt6%2B/kkpaULBoRFs0bE8CbbY9o5CIkQspESZPn6ydtgO6XUNRIXhUTFxiUr1jc3ZbaO9If0lg%2BXxAJS26F6kqJxcBGzJjQDULCMApFoAgtu7RHtK5konpzSk6Gx7ROamIcB7F2RXIthEch7AAiBAcQOCxzO91QRiUSj2ACEWKgANYAdwamFw6mIp1Y9HMAC8YhBDkQAHRhLDYABqBFSJFIixA9z27L2OBoewA%2BjyQsQ%2BRA7DQWWyORKjgAmADMewAKqQUaiEQA3BoEFiRRgInCkAiq7CYPaPZ57LwqUjfJimLxEBFWFhXRgsY0kA5MPbYXFEcUS9kiin1EJEI089WkJQgPb/X0AVkRI1IRzjwL2RxlaZURAgiz9/ulcoAsixTGqNVqda90K8kNgCFalKt1thOdhTK5mKgCNg7md/RzAzgO0wcExu73o6CHCnE0QKDGAbOkyngav05n0wB2RFHLdr/sD9OymNM3smozAYBGznGa9PC1e4Skcx7ZIhvunI/XKo0Ck0S9r0wfkbTtKM9kheM52TVMNzTWdV3zSUTzcNZSGYK4aC8ccak9DBhG9X1DwHQNUDQjCeSwnD0h5BpgHA2Nl3ndcMyzAFc3ufMuQ9CRiWwYVfyBJs1g2HkMBwaMkzFYj/XnbBW1Yg4RgpUwGhUYVm1E8TsDzGTkLlAB1VtTCeDZ4WuepQw4YQERCPZ0MNSNWzIPU9nRYgkDs7V0DRB0a1SNgvCMUMDj2SJlUxUhjWMXjUk/b9A1VBliAgOSdKQjl0KINZPUDACWCvMMQlte1OJk7iksZHkADFsM6IRgWwGgBPoGggSYGlo3JClauohqmukr8j0LPY3FLbL0JNOrcIOUhgB8DCEQgZJQ2ETV6D2aryVOVQAEkn0wd8bOtEqlF0oaSN/CkyNIdDhEo6aaLohFFL3ZE5opOiTTIWavjsjqcE%2BualCB%2Bi9wPC7/UDYMCOAiMQdhbAGg4vTByu4dO3HHsEZdUgUdODL2RG1RTN7B06ymvrPUiLBX3CtFIsweKj0ERsiDYK47IcmIVEwCAAewCkacwcxBu/CVAxMnyyZ5EYnWwaycxGDnzsJn9Wopa9Qn1VBw2SnMBdV8qmrfUn4VlyyFYwlq2osjmuuU5WiDF4aTx4ClRrrNFvqtb1THoMFiC9H09nwwhcKUAB6ecCEKyM1YIblA35JQeW9QUY7j4V2ed1lUYHEacXnFErgjTVtXPEJVU8Q1jTsqxW3Tq4w/yT0fqb0OJHoNWJUz%2B9wzUuD1b/NP1GLhwB8jbOVZ7tGNZh0M4bUikvFMTB5dS/U48ns7Z6J/OCxQr3UW%2BbljFfOiFuETkGw6IhCVeLf7xvBvg%2BIPefb2CNrUf2P%2B/hvOkNxYckTl/BoP9SLkXulReqTBaLA0AcA4BeVAJFVAvaT6pgRx8xoNKKUoJ0IOD2DiIOio/4xC/pqX6V8iDRjAFwN6EZwb0L2EIPYAdQjbjnBzCkHDmDoHBngo2QCOQjSlB7RUyolKpGAEwRWCJ6YYixHsCAwInQsAALQAXQOiCy7ZzrfiqKA5KTA5bjn4k7IE3VTjwljkwF2wDRjXntEPZcV1R7jyIDvVKixP6c1yjnIMdEAR3FTB/fKXinEhNcTuVUn8lBeG1AyfxrxgkuNZl/CBiSA7HH3B/dU3hsA7yHsnQiSoJ7w2npSApXh0rQgPvpPYu0z5gP1JWVsN07r31fKiDq6JPTunEBaVsxg36cwUfWEw0i7E3jrOhCkCyP6gIiTyKJGCQw8zvukG2QSNlL0jA4pBRMTzygph3DGo4uyviUJ5GgLj3Svy3kgIgGikDGGNKkHAodnjJFCDZD%2BEsroLzDPDCkhAaA0BiF2Ipq916hloMFVZaTd4NKPNDFgeyd4rzXhvGpRT4bCKOY0twx9T61lbE8l5bzRzXAIF8su7SEQNFbDAmaxUwIAo5Bk7%2Bdk8U70QUSgcoCeW5Sup0iirKnoIM5cgq6%2BVCrAXZRg0s2CIAyqJbgqUUpdroMfsqT4ew2BOlQCgahis9j0MYQ0ZhXBTboFUsAeWfkxnfNHK3Vhno%2BFcKdrwmYHVBFavVd%2BQlHJuIp1HhnJ%2BpIRTtU6kpSkpwRDyl8RojMuAwroE8AKgugbc3arHI4Og54bggybrmIEZblisKtEqBkrY5ZWUWhSPBLbA0HxGiWIgJqLVcFrSoFhDarb/IPsY1Ipj6jmP5jSKxykABKGKVCHO/FlHKCpSC1LVpuk8nbu30MrSwn69CS0Un3ba8Q9B6BLWwIaT0IRPmtmaRZeW8iDEsx%2BiahgddPTdUxPQVEU6cBLqPKOu9E6NgQA/fQTAM7KRjQvUB4BIHx3GHA5BzA/46owapOwHSHpjRoYw%2BOCkdKf4QD3T6ehQJ6EAEcvDEHoQholK7SCekVBu1FQruQmLMahzyUHCOoCw6cIgMdIh2lw%2B80OfH0MwM%2BiJq0rFFLkfo1wbNgqQFcbHTx/iBHZN4qw2EHDvjJO6bqhSPFxHjSKc3Ee249C1Pqf9Mx1j67sBq2c5tCQKgyqQzDWUku3iY17AFg7BNSaU1psXFBFcqYHOiLzXgou5SXFd1aeXRg3wC2Jx7JGE0TwXijMTfKYLNJm0JbbSI9kHm3pMEs5/W937lK/v/YbMl3GwP8SYAZozgj6kE2hCeDRQ3iHqHYP7VsygCoKSlAANgVL2RwUyhuprOKAvkrAOB8jgq9LVfIjUhD5HgtT2lVnoFogSPirjytSnuKaF4NBySlgIN8HYvxPMjB2rtIEs7sC0YWz5lVQ8tofb2vje4AABFVKkUg5jwZHeg6BgAhCEfcbiCOkdMAgMMljOHJLziBKpcwCPXTRkIA4Q5DbHyKUJ8T9Dzi1Vasp3cLVr72TY9We8BSm5scbbczJfMoCmfbc3Hg1EDBu5ariwGW4J6fQQB4KzgsMlQHs7eB2YX8EtWujYMjyX7mF2tlpBIWpuBbpkAZ1KakBxMA69MQcC9OijQo/bTJarO48EcHhFNo7x4pToFRC2vJ/OziQ6wZrdicOlAsEhc7043Eo%2BQp5A%2BeFmhrS53zK%2BRS6hjyIj2DwfMbvdxaoKT78wvWCbXZ8xKGKhISQKc3MiBmWISFEHxLxOv%2BMJR0DdSYF6m4a98VIJ9C7JIIM0lO%2Bd9vdT%2BuQxMiGC3y29ht8JHFPYP2En0Bcct2PEplkhEIL3qXn9u8H7%2Bp6E/nwowfzn8IWgLaExgDACxHcF%2BTABqlIrqoKgj839h4GhM0ou4sEVuTcGiQyY6Z%2Bp0bYoYDgRoZWH%2B9wXAyw9A3AcY/AfgXAOg5A6A3Aqglg1guUmk02MofA5AtCmBSBywqIIAcY4i0g0g8QMoW48QDBWgtB8QWgW4hg3A0g/AbAIAM24icY0gM2MocYYhWqAAHDNluFuLIBgVgTgVwPwFGFoGQdoEgeQHALACgBgDsAwDEJQNQHoR8IwLEBYFYEICQbIHQJvjzNQJEBoeQJECEA0OYNwKQS4awC%2BAAPKRC6B3weH8B6GKw%2BFMCEhOE4BibABwaXpBHkA4BGomCSAUEJG3ydCGhRipHegdDiZOEbIoGpEByRBKgvgeASSpExz8G8D8COQ0wqCNRJHAAcKgAUHLDypKD0jYDog%2BEjjxGCDCBiASCcAyByDCDKBqCaCpH6A8CGB3ggAWEEGGAECRBRiQDLD2oRzcD8DoCOT6g4BrHlrtCwIuCjjjB%2BCzFBAzDFClAGDJCMjpDnF3F5C4R9A3HzCVDVBdBTBPGzHHG4TdCNBvEDBlC2A/GeAtAGByxAnXEglSDLDCQtjwncFcBoHkAKE7HcB7B4GWGegygUgyAqL4DEA/SFgK78DkE6CLDLB1iuiDDlrUHSBbgUhxhxhaCCFsEJBMkJAygom8HolOFKEqEgBqGUmUEolSh8EgBbjiIzbclxiSGSGyjsHyGCnbHqFtFaGIAQAoCrBEAlRGFj76FmGGYcDcDqDSEaJyl7DACoCoB55xgUiSnkBGgkn7EGADGiDnojE2HyATEaBOEzHkDohKimBBHIGoHoFqlcA%2BF2glSsLcg4kEF7D4mEkQAeDGkUJkmLAUkaHUnkC0l6jUARlcD8n8FSjMkSEsE8A8BbhylbhsGJAYnYHqmqEalUklkyhRmpFCntnimOSpDODSBAA%3D%3D) (?)

[//]: # (Vertical slide)

```python
import ast
import sys
from typing import Set, Dict, List

class BackwardExitAnalyzer(ast.NodeVisitor):
    def __init__(self):
        # Tracks variables derived from user inputs that lead to an exit
        self.tainted_vars: Set[str] = set()
        # Maps variables to their source dependencies
        self.dependencies: Dict[str, Set[str]] = {}
        # Stores flagged dangerous entry points
        self.flagged_inputs: List[str] = []
        # Current function context
        self.current_function_args: Set[str] = set()

    def analyze(self, source_code: str):
        tree = ast.parse(source_code)
        # We process statements in reverse order within blocks to simulate a backward analysis
        self.visit(tree)
        return self.flagged_inputs

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Capture function arguments (potential FastAPI endpoints inputs)
        self.current_function_args = {arg.arg for arg in node.args.args}
        self.tainted_vars.clear()
        self.dependencies.clear()

        # Process the function body backwards
        for stmt in reversed(node.body):
            self.process_statement(stmt)

        self.generic_visit(node)

    def process_statement(self, stmt: ast.stmt):
        # 1. Check for explicit exit conditions/triggers
        if self._is_exit_trigger(stmt):
            # Extract variables involved in the exit condition or exit call
            trigger_vars = self._extract_vars(stmt)
            self.tainted_vars.update(trigger_vars)
            
            # Check if any argument directly triggered the exit
            for var in trigger_vars:
                if var in self.current_function_args:
                    self.flagged_inputs.append(f"Direct Exit Trigger via argument: '{var}' on line {stmt.lineno}")

        # 2. Track assignments backward (Data-flow step)
        elif isinstance(stmt, ast.Assign):
            targets = [self._extract_vars(t) for t in stmt.targets]
            flat_targets = {v for sublist in targets for v in sublist}
            value_vars = self._extract_vars(stmt.value)

            # If a variable currently known to cause an exit is being assigned here...
            if flat_targets.intersection(self.tainted_vars):
                # The exit dependency shifts to the right-hand side components
                self.tainted_vars.difference_update(flat_targets)
                self.tainted_vars.update(value_vars)

                # Check if the right-hand side variables are function inputs
                for var in value_vars:
                    if var in self.current_function_args:
                        self.flagged_inputs.append(
                            f"Input tracking match: argument '{var}' propagates to exit condition on line {stmt.lineno}"
                        )

    def _is_exit_trigger(self, node: ast.AST) -> bool:
        """Identifies sys.exit(), exit(), or raise statements."""
        # Match 'raise' statements
        if isinstance(node, ast.Raise):
            return True
        
        # Match 'exit()' or 'sys.exit()' calls (even inside If statements)
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id in ('exit', 'quit'):
                    return True
                if isinstance(child.func, ast.Attribute) and child.func.attr == 'exit':
                    if isinstance(child.func.value, ast.Name) and child.func.value.id == 'sys':
                        return True
        return False

    def _extract_vars(self, node: ast.AST) -> Set[str]:
        """Extracts all variable identifiers from an AST node."""
        return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


# --- Example Usage & Testing ---
if __name__ == "__main__":
    code_to_analyze = """
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/login")
def login(username: str, payload: dict):
    status = payload.get("status")
    user_type = username
    
    if status == "kill":
        sys.exit(1)
        
    if user_type == "admin":
        raise ValueError("No admins allowed")
        
    return {"message": "ok"}
    
@app.get("/safe")
def safe_route(x: int):
    y = x + 1
    return {"val": y}
"""

    analyzer = BackwardExitAnalyzer()
    findings = analyzer.analyze(code_to_analyze)

    print("--- Analysis Results ---")
    if findings:
        for finding in findings:
            print(f"[!] {finding}")
    else:
        print("[+] No exit-causing inputs detected.")

```

---

Obviously we can't know for the entire program.

For example if our constraint is 
`X != 4`
<!-- .element: class="fragment" -->
we can't know that
`X = C_GenerateKeyPair(input)`
satisfies this constraint.
<!-- .element: class="fragment" -->
but we **can** go up to a point and notify the programmer
<!-- .element: class="fragment" -->
i.e. a linting pass
<!-- .element: class="fragment" -->

---

- Run code in tests/dev server with sanitizers
- Fuzz test your end points
<!-- .element: class="fragment" -->
- Run static analyzers your code
<!-- .element: class="fragment" -->

