#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import pandas as pd
from fate.arch.storage import storage_ops


def min(block_table, block_indexes):
    map_ret = self._block_table.mapValues(lambda blocks: storage_ops.min(blocks[-1].storage, dim=0))
    reduce_ret = map_ret.reduce(lambda x, y: storage_ops.minimum(x, y))
    block_index_set = set(block_indexes)
    def _mapper(blocks):
        return [
            storage_ops.min(blocks[idx]) if idx in block_index_set else blocks[idx]
        ]

    def _reducer(lhs, rhs):
        ...

    block_table.mapValues(_mapper).reduce(_reducer)


def max(block_table, op_block_indexes):
    ...