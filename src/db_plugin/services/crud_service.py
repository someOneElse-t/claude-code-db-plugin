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

        # Strip schema prefix if present (e.g., "public.mytable" -> "mytable")
        table_name = table.split(".", 1)[-1] if "." in table else table

        dialect = self.executor.connection.get_dialect()

        # Ensure dialect's current_schema matches the table's schema
        if "." in table and hasattr(dialect, "current_schema"):
            dialect.current_schema = table.split(".", 1)[0]

        columns = dialect.get_columns(table_name)
        primary_keys = dialect.get_primary_keys(table_name)

        # If no PKs found, try querying without schema restriction
        if not primary_keys:
            result = dialect.execute_query(
                f"SELECT column_name FROM information_schema.key_column_usage "
                f"WHERE table_name = %s AND constraint_name IN ("
                f"SELECT constraint_name FROM information_schema.table_constraints "
                f"WHERE constraint_type = 'PRIMARY KEY' AND table_name = %s"
                f") ORDER BY ordinal_position",
                (table_name, table_name),
            )
            if not result.error_message:
                primary_keys = [row["column_name"] for row in result.rows]

        return TableSchema(
            name=table,
            columns=columns,
            primary_keys=primary_keys,
            indexes=[],
        )
