#  Copyright 2023 LanceDB Developers
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import unittest.mock as mock

import lance
import numpy as np
import pandas.testing as tm
import pyarrow as pa
import pytest

from lancedb.db import LanceDBConnection
from lancedb.query import LanceQueryBuilder
from lancedb.table import LanceTable


class MockTable:
    def __init__(self, tmp_path):
        self.uri = tmp_path
        self._conn = LanceDBConnection(self.uri)

    def to_lance(self):
        return lance.dataset(self.uri)

    def _execute_query(self, query):
        ds = self.to_lance()
        return ds.to_table(
            columns=query.columns,
            filter=query.filter,
            nearest={
                "column": query.vector_column,
                "q": query.vector,
                "k": query.k,
                "metric": query._metric,
                "nprobes": query.nprobes,
                "refine_factor": query.refine_factor,
            },
        )


@pytest.fixture
def table(tmp_path) -> MockTable:
    df = pa.table(
        {
            "vector": pa.array(
                [[1, 2], [3, 4]], type=pa.list_(pa.float32(), list_size=2)
            ),
            "id": pa.array([1, 2]),
            "str_field": pa.array(["a", "b"]),
            "float_field": pa.array([1.0, 2.0]),
        }
    )
    lance.write_dataset(df, tmp_path)
    return MockTable(tmp_path)


def test_query_builder(table):
    df = LanceQueryBuilder(table, [0, 0], "vector").limit(1).select(["id"]).to_df()
    assert df["id"].values[0] == 1
    assert all(df["vector"].values[0] == [1, 2])


def test_query_builder_with_filter(table):
    df = LanceQueryBuilder(table, [0, 0], "vector").where("id = 2").to_df()
    assert df["id"].values[0] == 2
    assert all(df["vector"].values[0] == [3, 4])


def test_query_builder_with_metric(table):
    query = [4, 8]
    vector_column_name = "vector"
    df_default = LanceQueryBuilder(table, query, vector_column_name).to_df()
    df_l2 = LanceQueryBuilder(table, query, vector_column_name).metric("L2").to_df()
    tm.assert_frame_equal(df_default, df_l2)

    df_cosine = (
        LanceQueryBuilder(table, query, vector_column_name)
        .metric("cosine")
        .limit(1)
        .to_df()
    )
    assert df_cosine.score[0] == pytest.approx(
        cosine_distance(query, df_cosine.vector[0]),
        abs=1e-6,
    )
    assert 0 <= df_cosine.score[0] <= 1


def test_query_builder_with_different_vector_column():
    table = mock.MagicMock(spec=LanceTable)
    query = [4, 8]
    vector_column_name = "foo_vector"
    builder = (
        LanceQueryBuilder(table, query, vector_column_name)
        .metric("cosine")
        .where("b < 10")
        .select(["b"])
        .limit(2)
    )
    ds = mock.Mock()
    table.to_lance.return_value = ds
    table._conn = mock.MagicMock()
    table._conn.is_managed_remote = False
    builder.to_arrow()
    ds.to_table.assert_called_once_with(
        columns=["b"],
        filter="b < 10",
        nearest={
            "column": vector_column_name,
            "q": query,
            "k": 2,
            "metric": "cosine",
            "nprobes": 20,
            "refine_factor": None,
        },
    )


def cosine_distance(vec1, vec2):
    return 1 - np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
