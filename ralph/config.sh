#!/bin/bash
# Per-repo Ralph configuration.
# This is the ONLY file you need to edit when copying the ralph/ folder
# into a new repo. The scripts source it automatically.

# Feedback-loop commands Claude must run before committing.
# One command per array entry; they appear verbatim in the prompt.
# Match these to the target repo's toolchain.
FEEDBACK_LOOPS=(
  "pip install -e '.[dev]' -q"
  "pytest tests/ -x -q --ignore=tests/integration"
)

# Container image used by afk.sh for the sandboxed run.
# Build once with: docker build -t redtape-ralph ralph/
# The Dockerfile layers uv onto node:22-bookworm-slim so both npx and uv work.
RALPH_IMAGE="redtape-ralph"

# Glob passed to `cat` to load issue files into the prompt.
# Override here if your issues live somewhere other than issues/*.md.
ISSUES_GLOB=".scratch/*/issues/*.md"
