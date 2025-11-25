# Contributing to MindOps

Thank you for your interest in contributing to MindOps!  We welcome
bug reports, feature requests and code improvements from the
community.  Please read the guidelines below before submitting a pull
request.

## Code Style

- **Python**: follow [PEP 8](https://peps.python.org/pep-0008/) and
  include type hints where possible.  Use black and isort for
  formatting.
- **Go**: follow the standard `gofmt` style.  Organise imports into
  standard library, third‑party and local packages.
- **YAML/Helm**: keep templates readable and avoid overly long lines.
- **Markdown**: wrap lines at 100 characters and use descriptive
  headings.

## Branching and Pull Requests

1. Fork the repository and create a branch off `main` for your change.
2. Make your changes, including tests if appropriate.
3. Open a pull request describing your change and link any related
   issues.
4. CI will run linting and tests automatically.  Please ensure your
   PR passes before requesting review.

## Reporting Issues

If you discover a bug or have a feature request, please open an
issue on GitHub with a clear description and steps to reproduce if
applicable.  Include which project you are referring to (e.g.
CAAT).