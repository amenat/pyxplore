#!/usr/bin/env python
"""
Figuring out which functions and methods are called the most is a good
starting point to jump into code base.

This script gives you broad count about which methods are called the
most, if you have same name for different functionalities then this will
likely give you false figures. However since AST can't easily parse from
where these function/methods are inherited, you need to co-relate them
with other data about imports/inheritance.
"""

import ast
import json
import sys
from collections import  Counter
from subprocess import getoutput


def parse_project(root):
    files = getoutput(f"find {root} -iname '*.py'").splitlines()

    calls = Counter()

    for file in files:
        calls.update(_get_calls_from_file(file))

    return calls.most_common()


def _get_calls_from_file(filename: str):

    tree = _open_and_parse_file(filename)
    calls = Counter()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if hasattr(node.func, "id"):
                calls[node.func.id] += 1
            elif hasattr(node.func, "attr"):
                calls[node.func.attr] += 1
            elif hasattr(node.func, "func"):
                continue # Ignore stupid edge case. func.getfunc(blah)()
            elif isinstance(node.func, ast.Subscript):
                continue # something[asda]()
            else:
                breakpoint()

    return calls


def _open_and_parse_file(filename: str) -> ast.Module:
    with open(filename) as file:
        tree = ast.parse(file.read())
    return tree


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} module_path")
        sys.exit(1)

    module_path = sys.argv[1]
    calls = parse_project(module_path)

    output_file = "calls.json"
    with open(output_file, "w") as fp:
        json.dump(calls, fp)
        print(f"Calls summary extracted to {output_file}")
