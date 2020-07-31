# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import re
from typing import Dict, Pattern, Union

import libcst as cst
import libcst.matchers as m
from libcst.codemod._context import CodemodContext
from libcst.codemod._visitor import ContextAwareVisitor
from libcst.metadata import PositionProvider


class GatherCommentsVisitor(ContextAwareVisitor):
    """
    Collects all comments matching a certain regex and their line numbers.
    This visitor is useful for capturing special-purpose comments, for example
    ``noqa`` style lint suppression annotations.

    Standalone comments are assumed to affect the line following them, and
    inline ones are recorded with the line they are on.

    After visiting a CST, matching comments are collected in the ``comments``
    attribute.
    """

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, context: CodemodContext, comment_regex: str) -> None:
        super().__init__(context)

        #: Dictionary of comments found in the CST. Keys are line numbers,
        #: values are comment nodes.
        self.comments: Dict[int, cst.Comment] = {}

        self._comment_matcher: Pattern[str] = re.compile(comment_regex)

    @m.visit(m.EmptyLine(comment=m.DoesNotMatch(None)))
    @m.visit(m.TrailingWhitespace(comment=m.DoesNotMatch(None)))
    def visit_comment(self, node: Union[cst.EmptyLine, cst.TrailingWhitespace]) -> None:
        comment = node.comment
        assert comment is not None  # hello, type checker
        if not self._comment_matcher.match(comment.value):
            return
        line = self.get_metadata(PositionProvider, comment).start.line
        if isinstance(node, cst.EmptyLine):
            # Standalone comments refer to the next line
            line += 1
        self.comments[line] = comment
