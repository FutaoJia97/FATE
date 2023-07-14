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
#
import functools

from fate.arch.tensor.inside import Hist
from ._compress_block import compress_blocks
from .._dataframe import DataFrame
from ..manager import BlockType, DataManager


def hist(df: DataFrame, targets):
    data_manager = df.data_manager

    block_table, data_manager = _try_to_compress_table(df.block_table, data_manager)
    block_id = data_manager.infer_operable_blocks()[0]

    def _mapper(blocks, target, bid: int = None):
        histogram = Hist()
        histogram.update(blocks[bid], target)

        return histogram

    def _reducer(l_histogram, r_histogram):
        return l_histogram.merge(r_histogram)

    _mapper_func = functools.partial(_mapper, bid=block_id)

    return block_table.join(targets.shardings._data, _mapper_func).reduce(_reducer)


def _try_to_compress_table(block_table, data_manager: DataManager):
    block_indexes = data_manager.infer_operable_blocks()
    if len(block_indexes) == 1:
        return block_table, data_manager

    block_type = None
    for block_id in block_indexes:
        _type = data_manager.get_block(block_id).block_type
        if not BlockType.is_integer(_type):
            raise ValueError("To use hist interface, indexes type should be integer >= 0")

        if not block_type:
            block_type = _type
        elif block_type < _type:
            block_type = _type

    to_promote_types = []
    for bid in block_indexes:
        to_promote_types.append((bid, block_type))

    data_manager.promote_types(to_promote_types)
    block_table, data_manager = compress_blocks(block_table, data_manager)

    return block_table, data_manager
