
from typing import Protocol, Callable, LiteralString, override, Final, Iterable
from dataclasses import dataclass
import subprocess
from os import getenv as get_env
import os
import re
import traceback
import base64
import zlib

# parse slides
# if code block:
#   if python:
#       try exec; green; expect: red
#   if C++:
#       add to template.cpp;
#       compile
#       if compiles: green; else red;

type Code = str
type Markdown = str
type HTML = str

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
class CodeResult:
    compile_result: CompileResult | None
    run_result: RunResult | None
    @property
    def compiles(self) -> bool:
        if self.compile_result is not None: return self.compile_result.compiles
        if self.run_result is not None: return self.run_result.runs
        raise RuntimeError("CodeResult has neither compile_result nor run_result, assumed bug")
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

_DEFAULT_HANDLER:Final = DefaultHandler()

def handle_code(language: RuntimeLanguage, code:str, handler_registry: CodeHandlerRegistry | None = None):
    handler: CodeHandlerRegistry = _DEFAULT_HANDLER if handler_registry is None else handler_registry
    return handler.handle_code(language, code)

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

def _create_unique_file_name(code:Code) -> str:
    """
    create a unique file name based on the hash of the code
    """
    # use adler for speed and determinism
    b64_hash = base64.b64encode((zlib.adler32(code.encode("utf-8")).to_bytes(8, signed=True))).decode("utf-8")
    print(b64_hash)
    return b64_hash.replace("=", "").replace("/", "").replace("+", "")

def handle_cpp(code:Code) -> CodeResult:
    file_name = f"build/{_create_unique_file_name(code)}"
    source_file_name = f"{file_name}.cpp"
    exe_file_name = f"{file_name}"
    # obj_file_name = f"{file_name}.obj"
    if not os.path.exists(source_file_name):
        source = r"int main() {" f"\n{code}\n" "}" if "main" not in code else code
        with open(source_file_name, "w") as output:
            output.write(source)
    # if compile only use "-c" in the following command, we test compiling and linking for now 
    if not os.path.exists(exe_file_name):
        res = subprocess.run((_CPP_COMPILER, "-o" f"{exe_file_name}" , source_file_name), stderr=subprocess.PIPE)
        compile_result = CompileResult(str(res.stderr), res.returncode )
        if res.returncode != 0: return CodeResult(compile_result=compile_result, run_result=None)
    res = subprocess.run((f"./{exe_file_name}"), stderr=subprocess.PIPE)
    run_result = RunResult(str(res.stderr), res.returncode)
    return CodeResult(run_result=run_result, compile_result=CompileResult("Cached", 0))

def handle_python(code:str) -> CodeResult:
    print_result:str = ""
    exit_code:int = 0
    exit_str:str = ""
    def mock_print(*value:object, end:str="\n"):
        nonlocal print_result
        print_result += "".join((str(v) for v in value)) + end
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
        unwrapped_exception:list[str] = traceback.format_exception(e)
        return CodeResult(None, RunResult(print_result + "".join(unwrapped_exception), 1))

_DEFAULT_HANDLER.add_language("Cpp", handle_cpp)
_DEFAULT_HANDLER.add_language("C++", handle_cpp)
_DEFAULT_HANDLER.add_language("Python", handle_python)
_DEFAULT_HANDLER.add_language("py", handle_python)

def result_to_string(result:CodeResult, wants:str) -> str:
    wants = wants.lower()
    wants_options_compile = ("compile", "compiles", "compiling", "compile-error")
    wants_options_run = ("run", "running", "erroring", "runs")
    if wants in wants_options_compile: return "rayjs-compiling" if result.compiles else "rayjs-not-compiling"
    if wants in wants_options_run: return "rayjs-running" if result.runs else ("rayjs-erroring" if result.compiles else "rayjs-not-compiling")
    raise Exception(f"wants was ignored: {wants} was not one of {', '.join(wants_options_compile + wants_options_run)}")

_FIND_CODE_PATTERN = (
    r"(?:^```)(?P<lang>[A-Za-z+]{2,10})(?:.{0,20})$(?:\r?\n)(?P<code>(?:[^\`]){3,}?)(?:```$\n)(?:\<\!\-\- \.element: class=\")(?P<outclass>[ A-Za-z0-9\-_]*?)(?:\"\s?)(?P<wantstag>wants)(?:=\")(?P<outwants>[A-Za-z0-9\-_]*?)(?:\" \-\-\>)"
)
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
        reconstructed = reconstructed.replace(groups["outwants"], result_to_string(code_result, groups["outwants"]))
        reconstructed = reconstructed.replace(groups["wantstag"], "does")
        return reconstructed
    return _COMPILED_REGEX.sub(on_match, input)

def template_file_setup(base_template_file:str, reveal_js_path:str) -> str:
    with open(base_template_file, "r") as template_file:
        return template_file.read().replace("@__REVEAL_JS_PATH__@", reveal_js_path)

def fill_output_template(input_markdown:Markdown, template_file:HTML, output_file_name:str, *, title:str|None=None) -> None:
    title = title if title is not None else output_file_name.rsplit(".", 1)[0]
    with open(output_file_name, "w") as out_file:
        out_file.write(
            template_file.replace("@__MARKDOWN INPUT__@", input_markdown) # fill in markdown
            .replace("@__TITLE__@", title)   # give it a good title
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
    # We only need "css", "dist", "plugin" folders
    #  TODO: Only Get required folders
    clone = subprocess.run(
        (_GIT_PATH, "clone", "-b", version_tag, "-q", "--depth", "1", "--single-branch", repo_url , destination_folder),
        stderr=subprocess.PIPE
    )
    if clone.returncode == 0:
        return dest_dir
    print(f"Could not clone reveal.js, got {clone.stderr}, using CDN instead")
    return f"https://cdnjs.cloudflare.com/ajax/libs/reveal.js/{version_tag}/"

_REVEAL_JS_PATH:Final = _clone_reveal_js()
_IGNORE_FILE_STRING = "<!-- .ignore -->"

def create_markdown_data(input_file_name:str) -> Markdown|None:
    with open(input_file_name, "r") as in_file:
        markdown_file_data = in_file.read()
    if (markdown_file_data[0:len(_IGNORE_FILE_STRING)] == _IGNORE_FILE_STRING):
        return None
    return for_each_code_block(markdown_file_data, handle_code)

def prepend_markdown_file(file_name_to_prepend:str|None, markdown_data:Markdown, *, new_slide:str="---") -> Markdown:
    if file_name_to_prepend is None: return markdown_data
    with open(file_name_to_prepend) as prepend_file:
        prepend_data = prepend_file.read()
    return prepend_data + "\n" + new_slide + "\n" + markdown_data

def append_markdown_file(file_name_to_append:str|None, markdown_data:Markdown, *, new_slide:str="---") -> Markdown:
    if file_name_to_append is None: return markdown_data
    with open(file_name_to_append) as append_file:
        append_data = append_file.read()
    return markdown_data + "\n" + new_slide + "\n" + append_data

def create_html_file(
        markdown_data:Markdown, output_file_name:str, input_file_name:str, *, 
        template_file_name:str = "TemplateSlides.html.in",
        reveal_js_path:str = _REVEAL_JS_PATH
    ) -> None:
    print(f"Processing {input_file_name}"
            f" to {output_file_name} using template {template_file_name}"
        )
    template_half_filled = template_file_setup(template_file_name, reveal_js_path)
    fill_output_template(markdown_data, template_half_filled, output_file_name, title=input_file_name.rsplit(".", 1)[0])

_HTML ="""<html>
    <body>
        <h1>Contents Of Slides</h1>
        <ul>
            {links_str}
        </ul>
    </body>
</html>
"""
def clean_link(link:str) -> str:
    import random
    link = link.replace(".no-index.", ".").replace("no-index", "")
    link = link.rsplit(".", 1)[0].replace(" ", "_")
    if len(link) <= 2:
        return (
            "unknown"
            + str(base64.b64encode(random.randbytes(3)), encoding="ascii")
            .replace("=", "")
            .replace("/", "")
            .replace("+", "")
        )
    return link + ".html"


def create_contents_index(to_link_to:Iterable[str]) -> None:
    indexable = ['<li><a href="{link}">{link}</a></li>'.format(link=clean_link(link)) for link in to_link_to if not ("no-index" in link) ]
    comments = ['<!-- {link} -->'.format(link=clean_link(link)) for link in to_link_to if ("no-index" in link) ]
    links_str = "\n".join(indexable + comments)
    with open("index.html", "w") as index_file:
        index_file.write(_HTML.format(links_str=links_str))

def main() -> None:
    import argparse
    arg_parser = argparse.ArgumentParser(description="Create slides from markdown file with code blocks that can be compiled and executed.", add_help=True)
    arg_parser.add_argument("input_files", metavar="input_markdown_files", type=str, nargs="+", help="markdown files to process, wildcards are allowed")
    arg_parser.add_argument("-t", "--template", type=str, default="TemplateSlides.html.in", help="Specify the template file to use. Default is TemplateSlides.html.in")
    arg_parser.add_argument("-o", "--output-prefix", type=str, default="", help="Specify the output folder name.\n Default is this folder")
    arg_parser.add_argument("-r", "--reveal-js-path", type=str, default=_REVEAL_JS_PATH, help="Path to reveal.js folder.\n Defaults to cloning the reveal.js repo in build/reveal_js.")
    arg_parser.add_argument("-i", "--ignore", type=str, default="", help="glob pattern of files to ignore, useful for READMEs, defaults to nothing")
    arg_parser.add_argument("-n", "--no-index", action="store_true", help="If a contents index should be (re/)created, defaults to creating one")
    arg_parser.add_argument("-e", "--end-slide", type=str, default=None, help="A markdown file to append to the end of each created slide deck, useful for contact info etc.")
    arg_parser.add_argument("-b", "--begin-slide", type=str, default=None, help="A markdown file to prepend to the start of each created slide deck")

    arg_parser.add_argument("-v", "--version", action="version", version="BuildSlides 0.0.0")
    args = arg_parser.parse_args()

    input_files:set[str] = {f for f in args.input_files if os.path.isfile(f) and (f not in args.ignore)}
    # If we have an index we might have to write it again (more files) or not (rebuilding some files but not all)
    if not args.no_index:
        create_contents_index(input_files)

    for input_file in input_files:
        output_file = args.output_prefix + clean_link(input_file)
        markdown_data = create_markdown_data(input_file)
        if markdown_data is None:
            print(f"Ignoring file {input_file}")
            continue
        markdown_data = prepend_markdown_file(args.begin_slide, markdown_data)
        markdown_data = append_markdown_file(args.end_slide, markdown_data)
        create_html_file(markdown_data, output_file, input_file, template_file_name=args.template, reveal_js_path=args.reveal_js_path)

if __name__ == "__main__":
    main()

