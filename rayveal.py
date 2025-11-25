
from typing import Protocol, Callable, LiteralString, override, Final, Iterable, Any
from dataclasses import dataclass
import subprocess
from os import getenv as get_env
import os
import re
import traceback
import base64
import zlib
import io

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
        match string.lower():
            case "cpp" | "c++" | "cxx": self._value = "cpp"
            case "python" | "py": self._value = "python"
            case _: self._value = string.lower()

    def __str__(self) -> str:
        return self._value
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, RuntimeLanguage): return False
        return value._value == self._value
    
    def __hash__(self) -> int:
        return self._value.__hash__()
    def __repr__(self) -> str:
        return f"RuntimeLanguage({self._value})"

class CompileExecFlags: 
    """
    Flags to pass to the compiler or interpreter
    """
    flags: set[str] | dict[str,Any] = {}

class MetaData:
    data: dict[str, str] = {}
    def __repr__(self) -> str:
        return self.data.__repr__()

type Handler  = Callable[[str, CompileExecFlags|None, MetaData|None], CodeResult]
type Language = LiteralString | RuntimeLanguage

class CodeHandlerRegistry(Protocol):
    def handle_code(self, language:RuntimeLanguage, code:str,
                    flags: CompileExecFlags|None = None,
                    meta:MetaData| None = None) -> CodeResult: ...
    def add_language(self, language: LiteralString, handler: Handler) -> "CodeHandlerRegistry": ...

class DefaultHandler(CodeHandlerRegistry):
    def __init__(self):
        self.registry: dict[RuntimeLanguage, Handler] = {}

    @override
    def add_language(self, language:LiteralString, handler:Handler) -> "DefaultHandler":
        self.registry.update({RuntimeLanguage(str(language)): handler})
        return self

    @override
    def handle_code(self,
                    language: RuntimeLanguage,
                    code:str,
                    flags: CompileExecFlags|None = None,
                    meta:MetaData| None = None
                ) -> CodeResult:
        assert isinstance(language, RuntimeLanguage)
        handler = self.registry.get(language)
        if not handler:
            raise RuntimeError(
                f"Cannot handle code for this language: {language}\n"
                f"Available languages are: {', '.join((str(k) for k in self.registry.keys()))}"
                )
        return handler(code, flags, meta)

_DEFAULT_HANDLER:Final = DefaultHandler()

def handle_code(
        language: RuntimeLanguage,
        code:str,
        handler_registry: CodeHandlerRegistry | None = None,
        flags:CompileExecFlags|None = None,
        meta: MetaData|None = None
    ) -> CodeResult:
    handler: CodeHandlerRegistry = _DEFAULT_HANDLER if handler_registry is None else handler_registry
    return handler.handle_code(language, code, flags=flags, meta=meta)

def try_executable(exe_path:str) -> bool:
    try:
        res = subprocess.run((exe_path, "--version"), stdout=subprocess.DEVNULL)
        return res.returncode == 0
    except:
        return False # windows raises for some reason

def find_executable(exe_name:str) -> str | None:
    where = "whereis" if os.name != "nt" else "where"
    res = subprocess.run((where, exe_name), stdout=subprocess.PIPE, check=True)
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
    return link

def _create_unique_file_name(code:Code, meta:MetaData|None) -> str:
    """
    create a unique file name
    """
    
    meta_data = "".join({a+b for a,b in meta.data.items()}) if meta is not None else ""
    checksum = zlib.adler32((code+meta_data).encode("utf-8"))
    b64_hash = base64.b64encode(checksum.to_bytes(4, signed=False)).decode("utf-8")
    b64_hash = b64_hash.replace("=", "").replace("/", "").replace("+", "")
    if meta is not None and "filename" in meta.data.keys(): return meta.data["filename"] + b64_hash
    # use adler for speed and determinism
    return b64_hash

def make_source_code(code:Code, meta:MetaData|None) -> tuple[Code, bool]:
    if "main" in code: return (code, True)
    if meta is not None and bool(meta.data.get("no-main", False)): return (code, False)
    else: return (r"int main() {" f"\n{code}\n" "}", True)


def handle_cpp(code:Code,
                flags:CompileExecFlags|None = None,
                meta: MetaData|None = None
            ) -> CodeResult:
    file_name = f"build/{_create_unique_file_name(code, meta)}"
    source_file_name = f"{file_name}.cpp"
    exe_file_name = f"{file_name}"
    source, has_main = make_source_code(code, meta)
    # assumes no overlap with checksums
    if not os.path.exists(source_file_name):
        with open(source_file_name, "w") as output:
            output.write(source)
    if not os.path.exists(exe_file_name):
        exe_file_name += ".o" if not has_main else ""
        compile_args = (_CPP_COMPILER, f"-o{exe_file_name}", source_file_name)
        if not has_main:
            compile_args:tuple[str, ...] = compile_args + ("-c",)
        res = subprocess.run(compile_args, stderr=subprocess.PIPE)
        compile_result = CompileResult(f"Compiling {file_name}:\n" + res.stderr.decode(), res.returncode )
        if res.returncode != 0: return CodeResult(compile_result=compile_result, run_result=None)
    else:
        compile_result = CompileResult("Cached", 0)
    run_result = None
    if has_main:
        res = subprocess.run((f"./{exe_file_name}"), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        run_result = RunResult(f"Running {file_name}" + res.stderr.decode() + res.stdout.decode(), res.returncode)
    return CodeResult(run_result=run_result, compile_result=compile_result)

def handle_python(code:str,
                  flags:CompileExecFlags|None = None,
                  meta: MetaData|None = None
                ) -> CodeResult:
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
    def mock_open(file:str, mode:str="r", *args:Any, **kwargs:Any):
        to_return = "foo bar baz".encode()
        return io.BufferedReader(io.BytesIO(to_return), len(to_return))
    
    _locals = flags.flags.get("locals", None) if flags and isinstance(flags.flags, dict) else None
    _globals:dict[str,Any] = flags.flags.get("globals", {}) if flags and isinstance(flags.flags, dict) else {}
    assert isinstance(_globals, dict)
    _globals.update({"print": mock_print, "exit":mock_exit, "open": mock_open})
    try:
        exec(code, _globals, _locals)
        return CodeResult(None, RunResult(print_result + exit_str, exit_code))
    except Exception as e:
        unwrapped_exception:list[str] = traceback.format_exception(e)
        return CodeResult(None, RunResult(print_result + "".join(unwrapped_exception), 1))

_DEFAULT_HANDLER.add_language("Cpp", handle_cpp)
_DEFAULT_HANDLER.add_language("C++", handle_cpp)
_DEFAULT_HANDLER.add_language("Python", handle_python)
_DEFAULT_HANDLER.add_language("py", handle_python)

def result_to_string(result:CodeResult, wants:str) -> str:
    _wants = set(wants.lower().split())

    assert_compile_tags = {"compiles", "compiling"}
    assert_run_tags = {"running", "runs"}
    assert_error_tags = {"erroring", "errors", "error"}
    assert_fails_compile_tags = {"not-compiling", "not-compiles", "not-compile", "does-not-compile", "compile-error"}
    run_tags = {"run",}
    compile_tags = {"compile",}
    all = assert_compile_tags | assert_run_tags | assert_error_tags | assert_fails_compile_tags | run_tags | compile_tags
    _wants.intersection_update(all)
    if len(_wants) == 0: raise Exception(f"wants was ignored: {wants} does not include one of {', '.join(all)}")
    if len(_wants) > 1: raise Exception(f"wants was ignored: {wants} includes two (not one) of {', '.join(all)}")
    want = next(iter(_wants))
    def create_exception(msg:str) -> Exception:
        compile_msg =  "" if result.compile_result is None else result.compile_result.compiler_output 
        run_msg = "" if result.run_result is None else result.run_result.run_output
        run_code = "" if result.run_result is None or result.runs else result.run_result.return_code
        return Exception(f'{msg} because wants contains "{want}" (in {wants})\n'
                         f' \n\nCOMPILE:\n {compile_msg}\n\nRUNNING: {run_msg}\n\n'
                         f' Code: {run_code}')

    if want in assert_compile_tags:
        if not result.compiles: raise create_exception(f'Code did not compile but expected to')
        return "rayjs-compiling"
    if want in assert_run_tags:
        if not result.runs: raise create_exception(f'Code did not run but expected to')
        return "rayjs-running"
    if want in assert_error_tags:
        if result.runs: raise create_exception(f'Code ran but expected to error')
        return "rayjs-erroring"
    if want in assert_fails_compile_tags:
        if result.compiles: raise create_exception(f'Code compiled but expected to not compile')
        return "rayjs-not-compiling"
    if want in run_tags:
        return "rayjs-running" if result.runs else ("rayjs-erroring" if result.compiles else "rayjs-not-compiling")
    if want in compile_tags:
        return "rayjs-compiling" if result.compiles else "rayjs-not-compiling"
    
    raise Exception(f"wants was ignored: {want} extracted from {wants} was not one of {', '.join(all)}\n This should never occur")



_FIND_CODE_PATTERN = (
    r"(?:^```)(?P<lang>[A-Za-z+]{2,10})(?:.{0,40})$(?:\r?\n)(?P<code>(?:[^\`]){3,}?)(?:```$\n)(?:\<\!\-\- \.element: )(?:(?:class=\")(?P<outclass>[ A-Za-z0-9\-_]*?)(?:\"\s?))?(?P<wantstag>wants)(?:=\")(?P<outwants>[-\s\w]*?)(?:\")(?:(?:\s+id=)(?P<id>[\"'\w]+))?(?: \-\-\>)"
)

_COMPILED_REGEX = re.compile(_FIND_CODE_PATTERN, re.MULTILINE)

def for_each_code_block(
            input:Markdown,
            meta:MetaData|None=None,
            code_handler: CodeHandlerRegistry | None = None,
        ) -> Markdown:
    previous_language_data: dict[Language, dict[str, Code]] = {}
    def on_match(full_match:re.Match[str]) -> str:
        groups = full_match.groupdict()
        reconstructed = full_match.string[full_match.start():full_match.end()]
        language = groups["lang"]
        wants = groups["outwants"].lower().replace("_", "-")
        if "nothing" in wants:
            print("Did not run code for language: ", language, " because wants was ", groups["outwants"])
            return reconstructed
        language = RuntimeLanguage(language)
        code :Code = groups["code"]
        id:str = groups["id"] if groups["id"] is not None else "last"
        id = id.replace('"', "").lower()
        if "append" in wants:
            # get the next word after append, else "last"
            if (start := wants.find("append-")) > 0:
                raw_id = wants[start:].removeprefix("append-").replace(" ", "")
                if len(raw_id) > 0:
                    id_to_append = str(raw_id).lower()
                else:
                    print("wants contains append- but no id was given, possible bug")
                    id_to_append = "last"
            else: id_to_append = "last"

            # Add the code we want to append to this code
            try:
                code = previous_language_data[language][id_to_append] + code
            except KeyError as e:
                raise KeyError(f"Lookup language={language=}      "
                               f"Keys: {previous_language_data.keys()=}"
                               ) from e
            # it can then be stored as this code's id
            #  so if we append again it still works
        previous_language_data.setdefault(language, {})[id] = code
        if id != "last": previous_language_data.setdefault(language, {})["last"] = code
        # print("Set data")
        _meta = meta
        if "no-main" in wants:
            _meta = MetaData() if meta is None else meta
            _meta.data["no-main"] = "True"
        # flags are None for now, expected to be populated via regex
        code_result:CodeResult = handle_code(language, code, code_handler, flags=None, meta=_meta)
        try:
            reconstructed = reconstructed.replace(groups["outwants"], result_to_string(code_result, groups["outwants"]))
            reconstructed = reconstructed.replace(groups["wantstag"], "does")
        except Exception as e:
            msg = "Could not process code block for file {file}\n code {code}"
            if meta is not None: raise Exception(msg.format(file=meta.data.get('filename', 'unknown file'), code=code)) from e
            else: raise e
        return reconstructed
    
    completed_block:str = _COMPILED_REGEX.sub(on_match, input)
    if "wants=" in completed_block:
        want_blocks = [ a for a in completed_block.splitlines() if "wants=" in a and "--" in a ]
        print("Warning: Some code blocks were not processed.\n"
              "\t Likely due to malformed element tag: order must be class, wants, id."
              "\t Note code blocks CANNOT contain backticks")
        print("Unprocessed blocks:\n", "\n\t".join(want_blocks))
        if meta is not None: print(f"in file {meta.data.get('filename', 'unknown file')}")
    return completed_block


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
    meta = MetaData()
    meta.data.update({"filename": clean_link(input_file_name)})
    return for_each_code_block(markdown_file_data, meta=meta)

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

def create_contents_index(to_link_to:Iterable[str]) -> None:
    indexable = ['<li><a href="{link}">{link}</a></li>'.format(link=clean_link(link) + ".html") for link in to_link_to if not ("no-index" in link) ]
    comments = ['<!-- {link} -->'.format(link=clean_link(link) + ".html") for link in to_link_to if ("no-index" in link) ]
    links_str = "\n".join(indexable + comments)
    with open("index.html", "w") as index_file:
        index_file.write(_HTML.format(links_str=links_str))

def main() -> None:
    import argparse
    arg_parser = argparse.ArgumentParser(prog="Rayveal.js.py", description="Create slides from markdown file with code blocks that can be compiled and executed.", add_help=True)
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
        try:
            output_file = args.output_prefix + clean_link(input_file) + ".html"
            print(f"Processing {input_file}")
            markdown_data = create_markdown_data(input_file)
            if markdown_data is None:
                print(f"Ignored file {input_file}")
                continue
            markdown_data = prepend_markdown_file(args.begin_slide, markdown_data)
            markdown_data = append_markdown_file(args.end_slide, markdown_data)
            create_html_file(markdown_data, output_file, input_file, template_file_name=args.template, reveal_js_path=args.reveal_js_path)
        except Exception as e:
            print(f"Could not process {input_file}")
            raise e

if __name__ == "__main__":
    main()

