"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from __future__ import annotations

import random

from ._ugbc_data import blocks

# A glitch on Bedrock where you can transform a falling block into any block
#
# REF: https://www.youtube.com/watch?v=U2VtWkkHhvY


class UGBC:
    def __init__(self) -> None:
        self.blocks: list[UGBCBlock] = []
        self.weight: list[int] = []
        for b in blocks:
            block = UGBCBlock.of(b)
            self.blocks.append(block)
            self.weight.append(block.weight)

    def randomize(self) -> UGBCBlock:
        return random.choices(self.blocks, self.weight)[0]


class UGBCBlock:
    def __init__(self, id: str, weight: int) -> None:
        self.id: str = id
        self.weight: int = weight

    @classmethod
    def of(cls, string: str) -> UGBCBlock:
        split = string.split(":")
        return cls(id=split[0], weight=int(split[1]))
