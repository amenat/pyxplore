#!/usr/bin/env python

import ast
import json
import os
import sys
from subprocess import getoutput
from typing import List, Union, Dict

FunctionDef = Union[ast.FunctionDef, ast.AsyncFunctionDef]
FunctionTypes = (ast.FunctionDef, ast.AsyncFunctionDef)
DocStringTypes = Union[FunctionDef, ast.ClassDef]
QualifiedPath = str
DocString = str


def parse_project(root) -> Dict[QualifiedPath, DocString]:
    """ Extract documentation from all '*.py' files in specified python module
        and return as dictionary.
    """
    files = getoutput(f"find {root} -iname '*.py'").splitlines()

    doc_strings = dict()

    for file in files:
        prefix = _create_prefix_from_path(file, root)
        doc_strings.update(get_all_docstrings(file, prefix=prefix))

    return doc_strings


def _create_prefix_from_path(path: str, root: str) -> str:
    file_rel_path = os.path.relpath(path, root)
    prefix = _clean_path_and_make_prefix(file_rel_path, root)
    return prefix


def _clean_path_and_make_prefix(prefix: str, root) -> str:
    prefix = prefix.replace('/', '.')

    # add main module name
    module = os.path.basename(os.path.normpath(root))
    prefix = module + '.' + prefix

    # remove file extension
    if prefix.endswith('py'):
        prefix = prefix[:-2]

    # handle __init__.py files
    if prefix.endswith('__init__.'):
        prefix = prefix[:-9]

    return prefix


def get_all_docstrings(filename: str, prefix: str) -> Dict[QualifiedPath, DocString]:
    """Given a file, parse all its functions, classes and methods to extract
    docstrings from them.

    Optional prefix is applied to all paths names.
    E.g. if prefix = "re", then compile function will become re.compile.
    """

    tree = _open_and_parse_file(filename)
    doc_strings = dict()

    # Capture module level docstring if it exists
    if isinstance(tree, ast.Module):
        doc_strings[prefix[:-1]] = ast.get_docstring(tree)


    functions = _filter_nodes(tree, FunctionTypes)
    doc_strings.update({prefix + function.name: ast.get_docstring(function)
                        for function in functions})

    classes = _filter_nodes(tree, ast.ClassDef)
    doc_strings.update({prefix + cls_tree.name: ast.get_docstring(cls_tree)
                        for cls_tree in classes})

    for cls_tree in classes:
        methods = _filter_nodes(cls_tree, FunctionTypes)
        doc_strings.update({prefix + cls_tree.name + "." + method.name: ast.get_docstring(method)
                            for method in methods})

    return doc_strings


def _open_and_parse_file(filename: str) -> ast.AST:
    with open(filename) as file:
        tree = ast.parse(file.read())
    return tree


def _filter_nodes(tree: ast.AST, nodetype: DocStringTypes) -> List[DocStringTypes]:
    nodes = [node for node in tree.body
             if isinstance(node, nodetype)]
    return nodes


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} module_path")
        sys.exit(1)

    module_path = sys.argv[1]
    docstrings = parse_project(module_path)

    output_file = "docstrings.json"
    with open(output_file, "w") as fp:
        json.dump(docstrings, fp)
        print(f"Docstrings extracted to {output_file}")
