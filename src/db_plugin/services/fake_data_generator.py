import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

from db_plugin.core.executor import QueryExecutor
from db_plugin.models.config import FakeDataConfig
from db_plugin.models.schema import ColumnSchema, TableSchema
from db_plugin.services import addresses

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".claude-code-db-plugin"
CONFIG_FILE = CONFIG_DIR / "fake_data_config.json"

# Cache for rule file contents: {file_path: [line1, line2, ...]}
_rule_file_cache: dict[str, list[str]] = {}


def _read_random_value_from_file(file_path: str) -> str:
    """Read a random line from a CSV-like rule file (one value per line)."""
    if file_path not in _rule_file_cache:
        try:
            lines = Path(file_path).read_text(encoding="utf-8").splitlines()
            lines = [l.strip() for l in lines if l.strip()]
            if not lines:
                logger.warning("Rule file '%s' is empty or unreadable", file_path)
                return ""
            _rule_file_cache[file_path] = lines
        except Exception as e:
            logger.warning("Failed to read rule file '%s': %s", file_path, e)
            return ""
    return random.choice(_rule_file_cache[file_path])

# Field name -> faker method mapping (used for extra_rules default values too)
FAKER_METHODS: list[str] = [
    "name", "first_name", "last_name", "user_name", "email", "phone_number",
    "address", "street_address", "city", "state", "country", "zipcode", "postalcode",
    "company", "company_suffix", "job", "url", "ipv4", "ipv6", "mac_address",
    "sentence", "paragraph", "text", "password", "uuid4", "date_time", "date",
    "date_of_birth", "time", "word", "domain_name", "file_name", "file_path",
    "color", "color_name", "currency_code", "language_name", "numerify",
    "random_digit", "random_int", "pyfloat", "pydecimal", "pybool",
    "credit_card_number", "bank_country", "bban", "iban", "swift",
    "isbn13", "isbn10", "vin", "license_plate", "ssn",
    "http_status_code", "http_method", "emoji", "md5", "sha1", "sha256",
    "slug", "hex_color", "image_url", "language_code",
    "latitude", "longitude", "timezone", "unix_time",
]

# Auto field name -> faker method mapping
FIELD_NAME_RULES: dict[str, str] = {
    "name": "name",
    "first_name": "first_name",
    "last_name": "last_name",
    "nickname": "first_name",
    "full_name": "name",
    "username": "user_name",
    "email": "email",
    "phone": "phone_number",
    "mobile": "phone_number",
    "tel": "phone_number",
    "fax": "phone_number",
    "address": "address_service",
    "street": "street_address",
    "city": "city",
    "state": "state",
    "province": "state",
    "country": "country",
    "zip": "zipcode",
    "postal_code": "zipcode",
    "company": "company",
    "employer": "company",
    "url": "url",
    "website": "url",
    "link": "url",
    "ip": "ipv4",
    "ip_address": "ipv4",
    "ipv6": "ipv6",
    "mac": "mac_address",
    "mac_address": "mac_address",
    "title": "sentence",
    "headline": "sentence",
    "subject": "sentence",
    "description": "text",
    "comment": "text",
    "content": "text",
    "body": "paragraph",
    "summary": "paragraph",
    "remark": "text",
    "note": "text",
    "password": "password",
    "pwd": "password",
    "secret": "password",
    "token": "uuid4",
    "access_token": "uuid4",
    "api_key": "sha256",
    "uuid": "uuid4",
    "hash": "md5",
    "checksum": "sha1",
    "signature": "sha256",
    "created_at": "date_time",
    "updated_at": "date_time",
    "deleted_at": "date_time",
    "date": "date",
    "birthday": "date_of_birth",
    "birth_date": "date_of_birth",
    "dob": "date_of_birth",
    "time": "time",
    "timestamp": "date_time",
    "expire": "date_time",
    "expires_at": "date_time",
    "start_date": "date",
    "end_date": "date",
    "job": "job",
    "occupation": "job",
    "position": "job",
    "role": "job",
    "currency": "currency_code",
    "amount": "pyfloat",
    "price": "pyfloat",
    "cost": "pyfloat",
    "balance": "pyfloat",
    "salary": "pyfloat",
    "total": "pyfloat",
    "fee": "pyfloat",
    "tax": "pyfloat",
    "discount": "pyfloat",
    "latitude": "latitude",
    "longitude": "longitude",
    "lat": "latitude",
    "lng": "longitude",
    "color": "color_name",
    "color_hex": "hex_color",
    "language": "language_name",
    "locale": "language_code",
    "timezone": "timezone",
    "slug": "slug",
    "file_name": "file_name",
    "file_path": "file_path",
    "file_url": "image_url",
    "avatar": "image_url",
    "image": "image_url",
    "icon": "image_url",
    "isbn": "isbn13",
    "license": "license_plate",
    "bank": "bban",
    "card_number": "credit_card_number",
    "ssn": "ssn",
    "id_card": "ssn",
}


def load_config() -> FakeDataConfig:
    """Load fake data config from disk."""
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return FakeDataConfig(**data)
        except Exception as e:
            logger.warning("Failed to load fake data config: %s", e)
    return FakeDataConfig()


def save_config(config: FakeDataConfig) -> None:
    """Save fake data config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps({
            "time_type": config.time_type,
            "int_mode": config.int_mode,
            "address_file": config.address_file,
            "extra_rules": config.extra_rules,
            "rule_files": config.rule_files,
        }, indent=2),
        encoding="utf-8",
    )
    logger.info("Saved fake data config to %s", CONFIG_FILE)


def _generate_time(time_type: int) -> str:
    """Generate a datetime string based on time_type config."""
    now = datetime.now()
    ranges = {
        0: (now, now),
        1: (now - timedelta(weeks=1), now),
        2: (now - timedelta(days=30), now),
        3: (now - timedelta(days=365), now),
        4: (now, now + timedelta(weeks=1)),
        5: (now, now + timedelta(days=30)),
        6: (now, now + timedelta(days=365)),
        7: (now - timedelta(weeks=1), now + timedelta(weeks=1)),
        8: (now - timedelta(days=30), now + timedelta(days=30)),
        9: (now - timedelta(days=365), now + timedelta(days=365)),
    }
    start, end = ranges.get(time_type, (now, now))
    if start == end:
        return start.strftime("%Y-%m-%d %H:%M:%S")
    delta = end - start
    random_dt = start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))
    return random_dt.strftime("%Y-%m-%d %H:%M:%S")


def _generate_int(int_mode: int) -> int:
    """Generate a random integer based on int_mode config."""
    if int_mode == 1:
        return random.randint(-99999, 99999)
    return random.randint(1, 99999)


def _generate_json(faker: Faker) -> str:
    """Generate a random JSON string."""
    return faker.json_bytes().decode("utf-8")


def _generate_enum_value(faker: Faker) -> str:
    """Generate a plausible enum-like string value."""
    return random.choice(["active", "inactive", "pending", "enabled", "disabled",
                          "draft", "published", "archived", "approved", "rejected",
                          "new", "used", "cancelled", "completed", "failed",
                          "yes", "no", "true", "false"])


def _generate_array(faker: Faker) -> str:
    """Generate a random array as a string representation (for PG-style arrays)."""
    count = random.randint(1, 4)
    items = [faker.word() for _ in range(count)]
    return "{" + ",".join(items) + "}"


def _is_time_column(col_lower: str, data_type: str) -> bool:
    """Check if column is likely a date/timestamp type based on name or type."""
    # Data type checks — match actual timestamp/date types
    for hint in ("timestamp", "datetime"):
        if hint in data_type:
            return True
    # Name-based checks — match columns that look like timestamps
    # (exclude pure time-type columns; they're handled separately)
    if data_type != "time":
        for hint in ("_at", "_date", "_time", "created", "updated", "deleted", "timestamp", "datetime"):
            if hint in col_lower:
                return True
    # USER-DEFINED with time-like names (common when DB introspection can't resolve the type)
    if data_type == "user-defined":
        for hint in ("_at", "_date", "_time", "created", "updated", "deleted"):
            if hint in col_lower:
                return True
    return False


def _is_id_auto_increment(col_lower: str, data_type: str, is_pk: bool) -> bool:
    """Check if this is an auto-increment PK column that should be skipped."""
    if col_lower != "id" or not is_pk:
        return False
    return any(t in data_type for t in ("int", "bigint", "smallint", "serial"))


def _is_id_uuid_type(col_lower: str, data_type: str, is_pk: bool) -> bool:
    """Check if this is a `id` column with varchar/uuid type that needs a generated UUID."""
    if col_lower != "id":
        return False
    return any(t in data_type for t in ("varchar", "char", "uuid", "string"))


def _generate_value(
    column: ColumnSchema,
    faker: Faker,
    config: FakeDataConfig,
) -> object:
    """Generate a fake value for a column, using config and field name rules."""
    col_lower = column.name.lower()
    data_type = column.data_type.lower()

    # 1. Check extra_rules first (user-defined)
    for pattern, method_name in config.extra_rules.items():
        if pattern.lower() in col_lower:
            method = getattr(faker, method_name, None)
            if method:
                value = method()
                if isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                return value

    # 1b. Check rule file mapping (column-specific rule files take priority)
    if col_lower in config.rule_files:
        return _read_random_value_from_file(config.rule_files[col_lower])

    # 2. Time column (timestamp/datetime) — checked before name-based rules
    #    to prevent FIELD_NAME_RULES["time"] from generating wrong format.
    if _is_time_column(col_lower, data_type):
        return _generate_time(config.time_type)

    # 2b. Pure time type (HH:MM:SS only)
    if data_type == "time":
        return faker.time()

    # 3. Check built-in field name rules
    for pattern, method_name in FIELD_NAME_RULES.items():
        if pattern in col_lower:
            if method_name == "address_service":
                return addresses.get_random_address()
            method = getattr(faker, method_name, None)
            if method:
                value = method()
                if isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                return value

    # 4. Integer column
    if data_type in ("integer", "bigint", "smallint", "serial", "int", "int2", "int4", "int8"):
        return _generate_int(config.int_mode)

    # 5. Float/numeric column
    if data_type in ("real", "double precision", "numeric", "decimal", "float", "float4", "float8", "money"):
        val = round(random.uniform(0, 9999), 2)
        return val if config.int_mode == 1 or val >= 0 else -val

    # 6. Boolean column
    if data_type in ("boolean", "bool"):
        return random.choice([True, False])

    # 7. JSON column
    if data_type in ("json", "jsonb"):
        return _generate_json(faker)

    # 8. Enum / status-like column
    if data_type in ("enum", "enum type", "user-defined"):
        if not any(hint in col_lower for hint in ("time", "date", "ts", "at")):
            return _generate_enum_value(faker)

    # 9. Array column (PostgreSQL-style)
    if data_type.startswith("array") or data_type.endswith("[]"):
        return _generate_array(faker)

    # 10. String/text column
    if data_type in ("text", "character varying", "varchar", "char", "character", "string", "uuid"):
        return faker.word()

    # 11. Binary/blob column
    if data_type in ("blob", "bytea", "binary", "varbinary", "longblob", "mediumblob", "tinyblob"):
        return faker.sha1()

    # 12. Unknown type
    logger.debug("Unknown data_type '%s' for column '%s', defaulting to string", column.data_type, column.name)
    return faker.word()


class FakeDataGenerator:
    """Generates fake data based on table schema and configuration."""

    def __init__(self, config: FakeDataConfig | None = None):
        self.config = config or FakeDataConfig()
        self.faker = Faker()

    def generate(self, table: TableSchema, count: int) -> list[dict]:
        """Generate fake records for the given table schema."""
        logger.info("Generating %d fake records for table '%s' (columns: %d, config.time_type=%d, config.int_mode=%d)",
                     count, table.name, len(table.columns), self.config.time_type, self.config.int_mode)
        for col in table.columns:
            col_lower = col.name.lower()
            data_type_lower = col.data_type.lower()
            is_auto_skip = _is_id_auto_increment(col_lower, data_type_lower, col.is_primary_key)
            is_uuid_gen = _is_id_uuid_type(col_lower, data_type_lower, col.is_primary_key)
            if is_auto_skip:
                logger.info("Column '%s' (type=%s) → AUTO-INCREMENT PK: will skip (DB auto-generates)",
                            col.name, col.data_type)
            elif is_uuid_gen:
                logger.info("Column '%s' (type=%s) → ID VARCHAR/UUID: will generate UUID (no hyphens)",
                            col.name, col.data_type)
            else:
                logger.debug("Column '%s' -> data_type='%s', is_nullable=%s, is_pk=%s",
                             col.name, col.data_type, col.is_nullable, col.is_primary_key)

        records = []
        for _ in range(count):
            record = {}
            for col in table.columns:
                if _is_id_auto_increment(col.name.lower(), col.data_type.lower(), col.is_primary_key):
                    continue
                if _is_id_uuid_type(col.name.lower(), col.data_type.lower(), col.is_primary_key):
                    record[col.name] = self.faker.uuid4().replace("-", "")
                    continue
                record[col.name] = _generate_value(col, self.faker, self.config)
            records.append(record)
        logger.info("Fake data generation complete: %d records", len(records))
        return records

    def generate_and_insert(
        self,
        table: TableSchema,
        count: int,
        executor: QueryExecutor,
    ) -> int:
        """Generate fake data and insert into the database. Returns count of inserted rows."""
        logger.info("Generating and inserting %d fake records into table '%s'", count, table.name)
        records = self.generate(table, count)
        dialect = executor.connection.get_dialect()
        inserted = 0
        errors = 0
        for record in records:
            insert_data = {
                k: v for k, v in record.items()
                if v is not None
            }
            result = dialect.insert(table.name, insert_data)
            if result.error_message is None:
                inserted += 1
            else:
                errors += 1
                logger.warning("Failed to insert fake record into '%s': %s", table.name, result.error_message)
        logger.info("Fake data insert complete: %d inserted, %d errors", inserted, errors)
        return inserted

    def generate_and_insert_batch(
        self,
        table: TableSchema,
        count: int,
        executor: QueryExecutor,
    ) -> int:
        """Generate fake data and insert using batch INSERT. Returns count of inserted rows."""
        logger.info("Generating and batch-inserting %d fake records into table '%s'", count, table.name)
        records = self.generate(table, count)
        dialect = executor.connection.get_dialect()
        if not records:
            logger.warning("No records generated for table '%s'", table.name)
            return 0

        inserted = 0
        errors = 0
        # Build batch insert SQL: INSERT INTO table (cols) VALUES (...), (...), ...
        # Split into batches of 100 to avoid query size limits
        batch_size = 100
        for batch_start in range(0, len(records), batch_size):
            batch = records[batch_start:batch_start + batch_size]
            placeholders = []
            all_values = []
            for record in batch:
                placeholders.append(f"({', '.join(['%s'] * len(record))})")
                all_values.extend(record.values())
            cols = ", ".join(self.quote_identifier_safe(dialect, k) for k in records[0].keys())
            sql = f"INSERT INTO {dialect.format_table_ref(table.name)} ({cols}) VALUES {', '.join(placeholders)}"
            try:
                result = dialect.execute_query(sql, tuple(all_values))
                if result.error_message:
                    # Fall back to individual inserts for failed batch
                    for record in batch:
                        single_result = dialect.insert(table.name, {k: v for k, v in record.items() if v is not None})
                        if single_result.error_message is None:
                            inserted += 1
                        else:
                            errors += 1
                            logger.warning("Failed to insert fake record into '%s': %s", table.name, single_result.error_message)
                else:
                    inserted += len(batch)
                    dialect.commit()
            except Exception as e:
                errors += len(batch)
                logger.warning("Batch insert failed for table '%s': %s, falling back to individual", table.name, e)
                for record in batch:
                    single_result = dialect.insert(table.name, {k: v for k, v in record.items() if v is not None})
                    if single_result.error_message is None:
                        inserted += 1
                    else:
                        errors += 1
                        logger.warning("Failed to insert fake record into '%s': %s", table.name, single_result.error_message)

        logger.info("Fake data batch insert complete: %d inserted, %d errors", inserted, errors)
        return inserted

    @staticmethod
    def quote_identifier_safe(dialect, name: str) -> str:
        """Safely quote an identifier, handling None values."""
        return dialect.quote_identifier(name)
