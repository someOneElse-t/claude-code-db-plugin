from db_plugin.core.executor import QueryExecutor
from db_plugin.models.result import QueryResult
from db_plugin.models.schema import TableSchema


class CRUDService:
    """Provides CRUD operations against a database."""

    def __init__(self, executor: QueryExecutor):
        self.executor = executor

    def create_record(self, table: str, data: dict) -> QueryResult:
        dialect = self.executor.connection.get_dialect()
        return dialect.insert(table, data)

    def read_records(
        self,
        table: str,
        where: dict | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> QueryResult:
        dialect = self.executor.connection.get_dialect()
        table_ref = dialect.format_table_ref(table)
        sql = f"SELECT * FROM {table_ref}"
        params: tuple = ()
        if where:
            conditions = " AND ".join(
                f"{dialect.quote_identifier(k)} = %s" for k in where.keys()
            )
            sql += f" WHERE {conditions}"
            params = tuple(where.values())
        sql += f" LIMIT {limit} OFFSET {offset}"
        return self.executor.execute(sql, params)

    def update_record(
        self,
        table: str,
        data: dict,
        primary_key_values: tuple,
        table_schema: TableSchema,
    ) -> QueryResult:
        pks = table_schema.primary_keys
        if not pks:
            raise ValueError(f"Table '{table}' has no primary key defined")
        where = dict(zip(pks, primary_key_values))
        dialect = self.executor.connection.get_dialect()
        return dialect.update(table, data, where)

    def delete_record(
        self,
        table: str,
        primary_key_values: tuple,
        table_schema: TableSchema,
    ) -> QueryResult:
        pks = table_schema.primary_keys
        if not pks:
            raise ValueError(f"Table '{table}' has no primary key defined")
        where = dict(zip(pks, primary_key_values))
        dialect = self.executor.connection.get_dialect()
        return dialect.delete(table, where)

    def get_schema(self, table: str) -> TableSchema:
        """Fetch table schema from the database."""
        from db_plugin.models.schema import ColumnSchema, TableSchema, IndexSchema

        dialect = self.executor.connection.get_dialect()
        columns = dialect.get_columns(table)
        primary_keys = dialect.get_primary_keys(table)
        return TableSchema(
            name=table,
            columns=columns,
            primary_keys=primary_keys,
            indexes=[],
        )
