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

from typing import Generic, TypeVar

EV = TypeVar("EV")
V = TypeVar("V")
PK = TypeVar("PK")
Coder = TypeVar("Coder")


class TensorEvaluator(Generic[EV, V, PK, Coder]):
    @staticmethod
    def add(a: EV, b: EV, pk: PK) -> EV:
        ...

    @staticmethod
    def add_plain(a: EV, b: V, pk: PK, coder: Coder, output_dtype=None) -> EV:
        ...

    @staticmethod
    def add_plain_scalar(a: EV, b, pk: PK, coder: Coder, output_dtype) -> EV:
        encoded = coder.encode(b, dtype=output_dtype)
        encrypted = pk.encrypt_encoded_scalar(encoded, obfuscate=False)
        return a.add_scalar(pk.pk, encrypted)
