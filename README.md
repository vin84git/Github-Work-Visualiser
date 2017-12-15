# Github Work Visualiser

This is a tool to help you visualise when a Github user worked on their projects.
It's much more convenient to watch this tool's output for a minute, than to dig
through Github, Finding graphs of when individual repositories were committed to.

## What you get

You get a dynamic graph, displaying commits on a user's repositories over time.
The final graph is the total number of commits per repository, in relation to
the number of commits commits of their largest repository.

![Demo](http://owenowen.netsoc.ie/github.gif)

## Requirements

* python 3.x

## Setup

```
pip install -r requirements.txt
```

## Run

```
./github.py
```

You can add `--fancy` if you want box drawing characters :)
