
from typing import Protocol, Callable, LiteralString, override, Final, Iterable
from dataclasses import dataclass
import subprocess
from os import getenv as get_env
import os
import re

# parse slides
# if code block:
#   if python:
#       try exec; green; expect: red
#   if C++:
#       add to template.cpp;
#       compile
#       if compiles: green; else red;


markdown_to_parse = """
```C++
/* compiles */
```
```C++
does not compile
```
```Cpp
/* compiles */
```
```Cpp
does not compile
```
# heading one
## heading two
---
something else
```py
print(1)
```
```Python
assert false
```
```py
exit(2)
```
```Py
exit("good bye")
```
"""
# parsed_markdown = parser.parse(markdown_to_parse)

# def filter_code(markdown:list["markdown_it.token.Token"]):
#     for token in markdown:
#         if token.tag == "code":
#             yield token
#         if token.children:
#             child_code = filter_code(token.children)
#             yield from child_code

@dataclass
class CompileResult:
    compiler_output: str
    return_code: int
    @property
    def compiles(self): return self.return_code == 0

@dataclass
class RunResult:
    run_output: str
    return_code: int
    @property
    def runs(self): return self.return_code == 0

@dataclass
class LinkResult:
    link_output: str
    return_code: int
    @property
    def links(self): return self.return_code == 0

@dataclass
class CodeResult:
    compile_result: CompileResult | None
    # link_result: LinkResult | None
    run_result: RunResult | None
    @property
    def compiles(self) -> bool:
        if self.compile_result is not None: return self.compile_result.compiles
        if self.run_result is not None: return self.run_result.runs
        return False # ?
    @property
    def runs(self) -> bool:
        if self.run_result is not None: return self.run_result.runs
        return False

class RuntimeLanguage:
    def __init__(self, string:str) -> None:
        if len(string) > 10 or ' ' in string:
            raise RuntimeError("Language did not fill appropriate requirements")
        self._value:str = string.lower()

    def __str__(self) -> str:
        return self._value
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, RuntimeLanguage): return False
        return value._value == self._value
    
    def __hash__(self) -> int:
        return self._value.__hash__()

type Handler  = Callable[[str], CodeResult]
# type RuntimeLanguage = str
type Language = LiteralString | RuntimeLanguage

class CodeHandlerRegistry(Protocol):
    def handle_code(self, language:RuntimeLanguage, code:str) -> CodeResult: ...
    def add_language(self, language: LiteralString, handler: Handler) -> "CodeHandlerRegistry": ...


class DefaultHandler(CodeHandlerRegistry):
    def __init__(self):
        self.registry: dict[RuntimeLanguage, Handler] = {}
    @override
    def add_language(self, language:LiteralString, handler:Handler) -> "DefaultHandler":
        self.registry.update({RuntimeLanguage(str(language)): handler})
        return self

    @override
    def handle_code(self, language:RuntimeLanguage, code:str) -> CodeResult:
        assert isinstance(language, RuntimeLanguage)
        handler = self.registry.get(language)
        if not handler:
            raise RuntimeError(
                f"Cannot handle code for this language: {language}\n"
                f"Available languages are: {', '.join((str(k) for k in self.registry.keys()))}"
                )
        return handler(code)

def handle_code(language: Language, code:str, handler_registry: CodeHandlerRegistry | None = None):
    handler: CodeHandlerRegistry = handle_code._default_handler if handler_registry is None else handler_registry
    return handler.handle_code(language, code)

handle_code._default_handler = DefaultHandler()

def try_executable(exe_path:str) -> bool:
    res = subprocess.run((exe_path, "--version"), stdout=subprocess.DEVNULL)
    return res.returncode == 0

def find_executable(exe_name:str) -> str | None:
    res = subprocess.run(("whereis", exe_name), stdout=subprocess.PIPE, check=True)
    if len(res.stdout) > len(exe_name) + 3:
        return str(res.stdout).replace(exe_name, "").replace(":", "").split()[0]

def _get_cpp_compiler() -> str:
    compiler = get_env("CXX")
    if compiler is not None: return compiler
    
    if try_executable("g++"): return "g++"
    if try_executable("clang++"): return "clang++"

    if compiler_path := find_executable("g++"): return compiler_path
    if compiler_path := find_executable("clang++"): return compiler_path
    raise RuntimeError("could not find C++ compiler")

_CPP_COMPILER:str = _get_cpp_compiler()

def handle_cpp(code:str, debug_value:str |None = None) -> CodeResult:
    handle_cpp._counter += 1
    file_name = debug_value if debug_value is not None else f"build/main_{handle_cpp._counter}"
    source_file_name = f"{file_name}.cpp"
    # obj_file_name = f"{file_name}.obj"
    exe_file_name = f"{file_name}"
    with open("template.cpp.in", "r") as template, open(source_file_name, "w") as output:
        output.write(template.read().replace("@input@", code))
    # if compile only use "-c" in the following command, we test compiling and linking for now 
    res = subprocess.run((_CPP_COMPILER, "-o" f"{exe_file_name}" , source_file_name), stderr=subprocess.PIPE)
    compile_result = CompileResult(str(res.stderr), res.returncode )
    if res.returncode != 0: return CodeResult(compile_result=compile_result, run_result=None)
    # breakpoint()
    res = subprocess.run((f"./{exe_file_name}"), stderr=subprocess.PIPE)
    run_result = RunResult(str(res.stderr), res.returncode)
    return CodeResult(run_result=run_result, compile_result=compile_result)

handle_cpp._counter = 0

def handle_python(code:str) -> CodeResult:
    print_result:str = ""
    exit_code:int = 0
    exit_str:str = ""
    def mock_print(*value:object):
        nonlocal print_result
        print_result += str(value[0])
    def mock_exit(value:int|str):
        nonlocal exit_code
        nonlocal exit_str
        if isinstance(value, int): 
            exit_code = value
            return
        exit_code = 1
        exit_str = value

    try:
        exec(code, {"print": mock_print, "exit":mock_exit})
        return CodeResult(None, RunResult(print_result + exit_str, exit_code))
    except Exception as e:
        return CodeResult(None, RunResult(print_result + e.__repr__(), 1))

handle_code._default_handler.add_language("Cpp", handle_cpp)
handle_code._default_handler.add_language("C++", handle_cpp)
handle_code._default_handler.add_language("Python", handle_python)
handle_code._default_handler.add_language("py", handle_python)

def result_to_string(result:CodeResult, wants:str) -> str:
    wants = wants.lower()
    wants_options = ("compile", "run")
    if wants not in wants_options:
        raise RuntimeError(f"Unknown wants value: {wants}, expected one of {', '.join(wants_options)}")
    
    if wants == "compile": return "rayjs-compiling" if result.compiles else "reyjs-not-compiling"
    if wants == "run": return "rayjs-running" if result.runs else "reyjs-erroring"

type Code = str
type Markdown = str

_FIND_CODE_PATTERN = r"(?:^```)(?P<lang>[A-Za-z+]{2,10})(?:.{0,20})$(?:\r?\n)(?P<code>(?:[^\`]){3,}?)(?:```$\n)(?:\<\!\-\- \.element: class=\")(?P<outclass>[A-Za-z0-9\-_]*?)(?:\")(?:\s?wants=\")(?P<outwants>[A-Za-z0-9\-_]*?)(?:\" \-\-\>)"
_COMPILED_REGEX = re.compile(_FIND_CODE_PATTERN, re.MULTILINE)

def for_each_code_block(input:Markdown, code_handler:Callable[[RuntimeLanguage, Code], CodeResult]):
    def on_match(full_match:re.Match[str]) -> str:
        groups = full_match.groupdict()
        reconstructed = full_match.string[full_match.start():full_match.end()]
        language = groups["lang"]
        if groups["outwants"].lower() == "nothing":
            print("Did not run code for language: ", language, " because wants was ", groups["outwants"])
            return reconstructed
        language = RuntimeLanguage(language)
        code :Code = groups["code"]
        code_result = code_handler(language, code)
        reconstructed = reconstructed.replace(groups["outclass"], result_to_string(code_result, groups["outwants"]))
        return reconstructed
    return _COMPILED_REGEX.sub(on_match, input)

def template_file_setup(base_template_file:str, reveal_js_path:str) -> str:
    with open(base_template_file, "r") as template_file:
        return template_file.read().replace("@__REVEAL_JS_PATH__@", reveal_js_path)

def fill_output_template(input_markdown:str, template_file:str, output_file_name:str) -> None:
    with open(output_file_name, "w") as out_file:
        out_file.write(
            template_file.replace("@__MARKDOWN INPUT__@", input_markdown) # fill in markdown
            .replace("@__TITLE__@", output_file_name.rsplit(".", 1)[0])   # give it a good title
        )

def _get_git_path() -> str:
    if try_executable("git"): return "git"
    if (path_ := find_executable("git")) is not None: return path_
    raise RuntimeError("Could not find git executable")

_GIT_PATH = _get_git_path()

def _clone_reveal_js(*, 
        destination_folder:str = "build/reveal_js",
        version_tag:str = "5.2.1",
        repo_url:str = "https://github.com/hakimel/reveal.js.git"
    ) -> str:
    dest_dir = destination_folder if destination_folder.endswith("/") else destination_folder + "/"
    if os.path.exists(destination_folder):
        return dest_dir
    clone = subprocess.run(
        (_GIT_PATH, "clone", "-b", version_tag, "-q", "--depth", "1", "--single-branch", repo_url , destination_folder),
        stderr=subprocess.PIPE
    )
    if clone.returncode == 0:
        return dest_dir
    print(f"Could not clone reveal.js, got {clone.stderr}, using CDN instead")
    return f"https://cdnjs.cloudflare.com/ajax/libs/reveal.js/{version_tag}/"

_REVEAL_JS_PATH:Final = _clone_reveal_js()

def create_markdown_file(input_file_name:str, *,
        template_file_name:str = "TemplateSlides.html.in",
        output_file_name:str = "index.html",
        reveal_js_path:str = _REVEAL_JS_PATH
    ) -> None:
    with open(input_file_name, "r") as in_file:
        markdown_file_data = in_file.read()
        new_markdown_data = for_each_code_block(markdown_file_data, handle_code)
    template_half_filled = template_file_setup(template_file_name, reveal_js_path)
    fill_output_template(new_markdown_data, template_half_filled, output_file_name)

def create_contents_index(to_link_to:Iterable[str]) -> None:
    links = [f'<li><a href="{link}.html">{link}</a></li>' for link in to_link_to]
    links_str = "\n".join(links)
    with open("index.html", "w") as index_file:
        index_file.write(
f"""
<html>
    <body>
        <h1>Contents Of Slides</h1>
        <ul>
            {links_str}
        </ul>
    </body>
</html>
"""
        )


_HELP = (
"""
Create slides from markdown file with code blocks that can be compiled and executed.
Usage: BuildSlides.py [options] <input_markdown_files>
Options:
-t --template <template_file>
    Specify the template file to use. Default is TemplateSlides.html.in
-o --output <output_file>
    Specify the output file name. Default is index.html
input_markdown_files
    One or more markdown files to process.
-h --help
    Show this help message.
"""
)

def main() -> None:
    import argparse
    arg_parser = argparse.ArgumentParser(description="Create slides from markdown file with code blocks that can be compiled and executed.", add_help=False)
    arg_parser.add_argument("input_files", metavar="input_markdown_files", type=str, nargs="+", help="One or more markdown files to process.")
    arg_parser.add_argument("-t", "--template", type=str, default="TemplateSlides.html.in", help="Specify the template file to use. Default is TemplateSlides.html.in")
    arg_parser.add_argument("-o", "--output", type=str, default="index.html", help="Specify the output file name. Default is index.html")
    arg_parser.add_argument("-r", "--reveal-js-path", type=str, default=_REVEAL_JS_PATH, help="Path to reveal.js folder or CDN URL. Default is to clone reveal.js repo.")
    arg_parser.add_argument("-h", "--help", action="store_true", help="Show this help message.") 
    args = arg_parser.parse_args()
    if args.help:
        print(_HELP)
        exit(1)

    input_files:set[str] = {f for f in args.input_files if os.path.isfile(f) and f.endswith(".md")}
    single_file = True
    if len(input_files) != 1:
        single_file = False
        # Create an index.html file if one would otherwise not be created
        if not os.path.exists("index.html"):
            create_contents_index(input_files)

    for input_file in input_files:
        output_file = args.output if single_file else input_file.rsplit(".", 1)[0] + ".html"
        print(f"Processing {input_file} to {output_file} using template {args.template}")
        create_markdown_file(input_file, template_file_name=args.template, output_file_name=output_file, reveal_js_path=args.reveal_js_path)

if __name__ == "__main__":
    main()

