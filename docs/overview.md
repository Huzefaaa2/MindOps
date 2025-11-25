# MindOps Documentation Overview

This `docs/` directory collects shared documentation for the MindOps
repository.  Each project may have its own `docs` subfolder with
detailed information, tutorials and API references; this top‑level
directory provides general guidance and context for contributors and
users.

## Projects

MindOps is composed of several distinct research projects exploring
autonomous observability and cognitive operations.  Project 1
(CAAT) is the only implemented project as of November 2025, but
placeholders exist for upcoming efforts.  See the root
[`README.md`](../README.md) for a list of projects and their
descriptions.  When new projects are added, they should include
their own documentation in `projects/<name>/docs`.

## Architecture Diagrams

For CAAT and subsequent projects, architecture diagrams are stored in
`projects/<name>/docs/images`.  These images can be referenced from
Markdown files to illustrate component interactions.  For example,
the CAAT architecture diagram appears in
[`projects/caat/README.md`](../projects/caat/README.md).

## Contribution Guidelines

If you would like to contribute to MindOps, please read
[`contributing.md`](contributing.md).  It covers code style, branch
workflow, how to open pull requests and other best practices.