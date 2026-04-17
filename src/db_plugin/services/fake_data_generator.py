import random
from datetime import datetime, timedelta

from faker import Faker

from db_plugin.core.executor import QueryExecutor
from db_plugin.models.schema import ColumnSchema, TableSchema


# Field name -> faker method mapping
FIELD_NAME_RULES: dict[str, str] = {
    "name": "name",
    "username": "user_name",
    "email": "email",
    "phone": "phone_number",
    "mobile": "phone_number",
    "address": "address",
    "city": "city",
    "country": "country",
    "zip": "zipcode",
    "postal_code": "zipcode",
    "company": "company",
    "url": "url",
    "ip": "ipv4",
    "title": "sentence",
    "description": "text",
    "comment": "text",
    "password": "password",
    "token": "uuid4",
    "uuid": "uuid4",
    "created_at": "date_time",
    "updated_at": "date_time",
    "date": "date",
    "birthday": "date_of_birth",
}


def _generate_value(column: ColumnSchema, faker: Faker = None) -> any:
    """Generate a fake value for a column, using field name rules or data type fallback."""
    if faker is None:
        faker = Faker()

    # Try field name match
    col_lower = column.name.lower()
    for pattern, method_name in FIELD_NAME_RULES.items():
        if pattern in col_lower:
            method = getattr(faker, method_name, None)
            if method:
                value = method()
                # Convert to string for database insertion where needed
                if isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                return value

    # Fallback to data type
    data_type = column.data_type.lower()
    if data_type in ("integer", "bigint", "smallint", "serial"):
        return random.randint(1, 99999)
    elif data_type in ("real", "double precision", "numeric", "decimal", "float"):
        return round(random.uniform(0, 9999), 2)
    elif data_type in ("boolean", "bool"):
        return random.choice([True, False])
    elif data_type in ("date",):
        start = datetime(2020, 1, 1)
        end = datetime(2026, 12, 31)
        delta = end - start
        random_date = start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))
        return random_date.strftime("%Y-%m-%d")
    elif "timestamp" in data_type:
        start = datetime(2020, 1, 1)
        end = datetime(2026, 12, 31)
        delta = end - start
        random_dt = start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))
        return random_dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        # Default to random string
        return faker.word()


class FakeDataGenerator:
    """Generates fake data based on table schema."""

    def __init__(self, custom_values: dict[str, any] | None = None):
        self.custom_values = custom_values or {}
        self.faker = Faker()

    def generate(self, table: TableSchema, count: int) -> list[dict]:
        """Generate fake records for the given table schema."""
        records = []
        for _ in range(count):
            record = {}
            for col in table.columns:
                if col.name in self.custom_values:
                    record[col.name] = self.custom_values[col.name]
                elif col.is_primary_key:
                    # Skip primary key if auto-increment, or generate UUID
                    if "uuid" in col.name.lower():
                        record[col.name] = str(self.faker.uuid4())
                    # else: let the database handle auto-increment
                else:
                    record[col.name] = _generate_value(col, self.faker)
            records.append(record)
        return records

    def generate_and_insert(
        self,
        table: TableSchema,
        count: int,
        executor: QueryExecutor,
    ) -> int:
        """Generate fake data and insert into the database. Returns count of inserted rows."""
        records = self.generate(table, count)
        dialect = executor.connection.get_dialect()
        inserted = 0
        for record in records:
            # Only insert non-primary-key columns if PK is auto-increment
            insert_data = {
                k: v for k, v in record.items()
                if not any(c.name == k and c.is_primary_key for c in table.columns)
                or v is not None
            }
            result = dialect.insert(table.name, insert_data)
            if result.error_message is None:
                inserted += 1
        return inserted
