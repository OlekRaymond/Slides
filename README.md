<!-- .ignore -->

# Rayveal.js

Rayveal.js is a simple python script that turns simple, standalone markdown into a slide deck.

## Features

- Markdown:
    Rayveal.js uses [reveal.js]() to render the markdown document.
- Static site:
    Despite being a markdown files, the reveal.js slide deck is a static site and thus can be served via github pages.
- Anti Slide-ware:
    Code can be compiled and/or ran at "build" time to show what is happening.
- Portable slides:
    Slides can be released as markdown files for websites, blogs, git-books or more easily converted to slides.
- Easy to write:
    Markdown is much easier to write than powerpoint slides, especially for developers.


## Output

Output comes as one or more html files, if given multiple markdown documents, we assume the user wants to create multiple slide decks so each slide deck is given it's own html file and a contents page, `index.html`, is generated.

## Usage:

### Example 1:
`python3 BuildSlides.py example.md`
outputs index.html and no other html files

### Example 2:
`python3 BuildSlides.py example1.md example2.md` outputs `index.html` which contains links to, the created, `example1.html` and `example2.html`

### Example 3:
`python3 BuildSlides.py *.md` has the exact same behaviour as if the user had typed out all the markdown files in the current directory

### Example 4:
For use without the python file on your hard drive use: `curl -L https://raw.githubusercontent.com/OlekRaymond/Slides/refs/heads/main/BuildSlides.py > BuildSlides.py` and also clone the template if not using a custom one with `curl -L https://raw.githubusercontent.com/OlekRaymond/Slides/refs/heads/main/TemplateSlides.html.in > TemplateSlides.html.in` then run as usual with the commands above.

## Advanced usage:

- Files can be ignored with the flag `--ignore <glob>` or by having `<!-- .ignore -->` as the first thing in the file
- If working on only one file, you may not want to overwrite `index.html` or build other files, for this you can use `--no-index`

