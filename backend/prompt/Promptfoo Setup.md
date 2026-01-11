---
created: 2026-01-05 23:06
type: reference
tags: [promptfoo, llm-eval, tools]
---

# Promptfoo Setup

## Quick Reference

- **Version**: 0.120.8
- **UI Port**: `localhost:15500`

## Commands

```bash
promptfoo init                    # create new config in current dir
promptfoo init --example getting-started   # start with example

promptfoo eval                    # run evaluation
promptfoo eval --no-cache         # re-run without cache

promptfoo view                    # open web UI

promptfoo cache clear             # clear cached responses
promptfoo list evals              # see past runs

promptfoo validate                # check config for errors
promptfoo share                   # generate shareable link
```

## Required

```bash
export OPENAI_API_KEY="sk-..."    # set before running
```
