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

from lancedb.db import DBConnection
import pyarrow as pa


class RemoteDBConnection(DBConnection):
    """A connection to a remote LanceDB database."""
    def __init__(self, db_name: str, api_key: str):
        self.db_name = db_name
        self.api_key = api_key

    def __repr__(self) -> str:
        return f"RemoveConnect(name={self.db_name})"

    def open_table(self, name: str) -> LanceTable:
        """Open a Lance Table in the database.

        Parameters
        ----------
        name: str
            The name of the table.

        Returns
        -------
        A LanceTable object representing the table.
        """
        raise NotImplementedError

    def create_table(
        self,
        name: str,
        data: DATA = None,
        schema: pa.Schema = None,
        mode: str = "create",
        on_bad_vectors: str = "error",
        fill_value: float = 0.0,
    ) -> LanceTable:
        raise NotImplementedError