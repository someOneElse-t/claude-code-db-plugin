# Claude Code DB Plugin

A desktop database management GUI tool built with PySide6, featuring a pluggable dialect architecture that supports multi-database connectivity, CRUD operations, SQL query execution, fake data generation, and data import/export.

[中文文档](README.zh.md)

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Dialect System](#dialect-system)
- [Data Models](#data-models)
- [Fake Data Generation](#fake-data-generation)
- [Supported Databases](#supported-databases)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Configuration & Storage](#configuration--storage)
- [API Usage Examples](#api-usage-examples)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-dialect architecture** — Plugin-style dialect system with a well-defined abstract interface. Ships with Kingbase and MySQL both fully implemented.
- **Connection management** — Save, load, test, and switch between multiple database connections. Configurations persist to `~/.claude-code-db-plugin/connections.json` with **passwords encrypted using Fernet symmetric encryption**.
- **SQL query execution** — Write and execute arbitrary SQL with parameterized queries (SQL injection safe), execution timing, result display, and automatic history tracking.
- **CRUD operations** — Full Create / Read / Update / Delete support with automatic primary key resolution and pagination. **Inline data editing with real-time PK conflict detection — auto-generates missing PKs on save**.
- **Fake data generation** — Schema-aware generation using 20+ field name patterns (name, email, phone, address, etc.) with data type fallbacks. **4407 built-in Chinese addresses**, configurable time ranges, integer modes, custom rules, and rule files. Preview before inserting.
- **Data import/export** — CSV, Excel, and JSON export; CSV and Excel import with automatic column mapping.
- **Query history** — SQLite-backed local history of all executed queries with search, favorite marking, and execution metadata.
- **Database object tree** — Left-panel dock showing tables and views, with right-click context menus and double-click to browse data.
- **Logging system** — `RotatingFileHandler` based logging to `logs/app.log`, 5MB max per file, 3 backups kept.

## Screenshots

```
┌─────────────────────────────────────────────────────────────────┐
│  Menu Bar  [File] [Edit] [Query] [Tools] [Help]                  │
├─────────────────────────────────────────────────────────────────┤
│  Toolbar  [Manage Conn] [Exec SQL] [Fake Data] [Import] [Export]│
├──────────┬──────────────────────────────────────────────────────┤
│          │  ┌────────────────────────────────────┐              │
│ Database │  │  Data Browser │   SQL Editor       │  (Tabs)     │
│ Object   │  │                                    │              │
│ ├ Tables │  │  Table: users        [Prev][Next]  │              │
│ │ ├users │  │  ┌──────────────────────────────────┤│              │
│ │ ├orders│  │  │ id │ name  │ email        │ addr││              │
│ │ └roles │  │  │ 1  │ Alice │ a@test.com   │ BJ  ││              │
│ ├ Views  │  │  │ 2  │ Bob   │ b@test.com   │ SH  ││              │
│          │  │  └──────────────────────────────────┤│              │
│          │  └────────────────────────────────────┘│              │
├──────────┴──────────────────────────────────────────────────────┤
│  Status Bar  [Connected: kingbase@localhost:54321/mydb] [Ready]  │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| GUI | PySide6 (Qt 6.6+) | Desktop application framework, Fusion style |
| Database driver | psycopg2-binary (2.9+) | Kingbase connection via PostgreSQL protocol |
| Database driver | pymysql (1.0+) | MySQL database connection |
| Fake data | Faker (20.0+) | Realistic test data generation |
| Excel I/O | openpyxl (3.1+) | Excel file read/write |
| Encryption | cryptography (3.4+) | Fernet symmetric encryption for password storage |
| Testing | pytest (7.0+) | Unit test framework |
| Python | 3.12+ | Language runtime, PEP 695 type hints |

## Architecture

### Layer Diagram

```
┌─────────────────────────────────────────────────┐
│  GUI Layer (PySide6)                            │
│  MainWindow, ObjectTree, DataBrowser, SqlEditor │
│  ConnectionDialog, FakeDataDialog, ImportExport  │
│         │                                       │
│         ▼ (calls services only)                 │
├─────────────────────────────────────────────────┤
│  Services Layer                                 │
│  ConnectionManager  │  CRUDService              │
│  FakeDataGenerator  │  ImportExportService      │
│  QueryHistoryService                            │
│         │                                       │
│         ▼ (uses models, calls core + dialects)  │
├─────────────────────────────────────────────────┤
│  Models Layer (dataclasses)                     │
│  ConnectionConfig  │  TableSchema / ColumnSchema│
│  QueryResult       │  QueryHistoryEntry         │
│  IndexSchema                                    │
├──────────────┬──────────────────────────────────┤
│  Core Layer │  ← depends on Models + Dialects  │
│  DatabaseConnection  │  QueryExecutor           │
├──────────────┴──────────────────────────────────┤
│  Dialects Layer (pluggable SQL implementations) │
│  DialectBase (ABC) → KingbaseDialect            │
│                     → MySQLDialect (placeholder)│
└─────────────────────────────────────────────────┘
```

**Dependency direction**: `GUI → Services → Models ← Core → Dialects`

GUI only talks to Services. Services use Models and Core. Core bridges to Dialects. Models have zero dependencies.

### Layer Responsibilities

| Layer | Key Classes | Responsibility |
|-------|-------------|----------------|
| **GUI** | `MainWindow`, `ObjectTreePanel`, `DataBrowserWidget`, `SqlEditorWidget`, `ConnectionDialog`, `FakeDataDialog`, `ImportExportDialog` | All UI components. No database logic — delegates to Services. Uses `QTableView` + custom `QAbstractTableModel` for results. |
| **Services** | `ConnectionManager`, `CRUDService`, `FakeDataGenerator`, `ImportExportService`, `QueryHistoryService` | Business logic. Connection persistence, CRUD with parameterized SQL, schema-aware data generation, file I/O, SQLite-backed history. |
| **Models** | `ConnectionConfig`, `TableSchema`, `ColumnSchema`, `IndexSchema`, `QueryResult`, `QueryHistoryEntry` | Pure `dataclass` definitions. No database connection, no business logic. Shared across all layers. |
| **Core** | `DatabaseConnection`, `QueryExecutor` | Connection lifecycle management (connect/close/commit/rollback). Query execution with parameterized SQL and `execute_many` support. |
| **Dialects** | `DialectBase`, `KingbaseDialect`, `MySQLDialect` | SQL dialect abstraction: identifier quoting, type mapping, metadata queries (tables/columns/primary keys/views), CRUD SQL generation. |

## Dialect System

### `DialectBase` Abstract Interface

All database dialects must implement 12 methods:

```python
class DialectBase(ABC):
    name: str              # Dialect identifier, e.g. "kingbase"
    quote_char: str        # Identifier quote: " for Kingbase, ` for MySQL

    def connect(self, config: ConnectionConfig) -> Any: ...
    def close(self) -> None: ...
    def execute_query(self, sql: str, params: tuple = ()) -> QueryResult: ...
    def get_tables(self) -> list[str]: ...
    def get_columns(self, table_name: str) -> list[ColumnSchema]: ...
    def get_views(self) -> list[str]: ...
    def get_primary_keys(self, table_name: str) -> list[str]: ...
    def insert(self, table: str, data: dict) -> QueryResult: ...
    def update(self, table: str, data: dict, where: dict) -> QueryResult: ...
    def delete(self, table: str, where: dict) -> QueryResult: ...
    def quote_identifier(self, name: str) -> str: ...
    def get_type_mapping(self) -> dict[str, type]: ...
```

### Implementing a New Dialect

1. Subclass `DialectBase`
2. Set `name` and `quote_char` class attributes
3. Implement all 12 abstract methods
4. Register in `DIALECT_REGISTRY` in `dialects/__init__.py`

```python
from db_plugin.dialects.dialect_base import DialectBase

class PostgresDialect(DialectBase):
    name = "postgres"
    quote_char = '"'
    # ... implement methods using psycopg2 or asyncpg
```

```python
# In dialects/__init__.py
DIALECT_REGISTRY = {
    "kingbase": KingbaseDialect,
    "mysql": MySQLDialect,
    "postgres": PostgresDialect,  # Add new dialect
}
```

### KingbaseDialect Details

- **Driver**: `psycopg2` with `RealDictCursor` for dict-based row access
- **Protocol**: Kingbase is PostgreSQL-compatible, so standard PostgreSQL connection parameters work
- **Metadata queries**: First attempts `sys_tables` (Kingbase-specific catalog), falls back to `pg_tables` for compatibility
- **SQL injection protection**: All CRUD operations use `%s` parameterized queries
- **Transaction handling**: `autocommit = False`; commit on success, rollback on error
- **Identifier quoting**: Uses double quotes `"` for all table/column names

### MySQLDialect Status

**Fully implemented** using `pymysql` driver:
- Complete metadata queries via `information_schema`
- Parameterized CRUD operations (backtick `` ` `` identifier quoting)
- Full MySQL type mapping (int, varchar, text, datetime, blob, etc.)
- Transaction handling (`autocommit = False`, commit on success, rollback on error)
- `charset=utf8mb4` support

## Data Models

### `ConnectionConfig`

```python
@dataclass
class ConnectionConfig:
    name: str                    # User-friendly connection name
    dialect_name: str            # "kingbase", "mysql", etc.
    host: str
    port: int
    username: str
    password: str
    database: str
    extra_params: dict           # Additional driver-specific parameters
```

### `TableSchema` / `ColumnSchema` / `IndexSchema`

```python
@dataclass
class ColumnSchema:
    name: str
    data_type: str
    is_nullable: bool = True
    default_value: str | None = None
    is_primary_key: bool = False
    comment: str = ""

@dataclass
class IndexSchema:
    name: str
    columns: list[str]
    is_unique: bool = False
    is_primary: bool = False

@dataclass
class TableSchema:
    name: str
    columns: list[ColumnSchema]
    primary_keys: list[str]
    indexes: list[IndexSchema]  # defaults to []
```

### `QueryResult`

```python
@dataclass
class QueryResult:
    columns: list[str]           # Column names from cursor.description
    rows: list[dict]             # Each row as {column_name: value}
    row_count: int               # cursor.rowcount
    execution_time_ms: float     # Time measured via time.monotonic()
    error_message: str | None    # None on success
```

### `QueryHistoryEntry`

```python
@dataclass
class QueryHistoryEntry:
    id: int
    sql: str
    connection_name: str
    timestamp: datetime
    status: str                # "success" | "error"
    execution_time_ms: float
    is_favorite: bool = False
```

## Fake Data Generation

The `FakeDataGenerator` uses a two-tier matching strategy:

### Tier 1: Field Name Pattern Matching

20+ built-in patterns that match column names to Faker methods:

| Column name contains | Generated value | Faker method |
|---------------------|-----------------|--------------|
| `name` | Person name | `faker.name()` |
| `username` | Username | `faker.user_name()` |
| `email` | Email address | `faker.email()` |
| `phone`, `mobile` | Phone number | `faker.phone_number()` |
| `address` | Street address | `faker.address()` |
| `city` | City name | `faker.city()` |
| `country` | Country name | `faker.country()` |
| `zip`, `postal_code` | Postal code | `faker.zipcode()` |
| `company` | Company name | `faker.company()` |
| `url` | URL | `faker.url()` |
| `ip` | IPv4 address | `faker.ipv4()` |
| `title` | Sentence | `faker.sentence()` |
| `description`, `comment` | Paragraph text | `faker.text()` |
| `password` | Password string | `faker.password()` |
| `token`, `uuid` | UUID v4 | `faker.uuid4()` |
| `created_at`, `updated_at` | Date-time | `faker.date_time()` |
| `date` | Date (2020–2026) | `faker.date()` |
| `birthday` | Date of birth | `faker.date_of_birth()` |

### Tier 2: Data Type Fallback

When no field name pattern matches:

| Data type | Generated value |
|-----------|----------------|
| `integer`, `bigint`, `smallint`, `serial` | Random int 1–99,999 |
| `real`, `double precision`, `numeric`, `decimal`, `float` | Random float 0.0–9999.99 |
| `boolean`, `bool` | Random True/False |
| `date` | Random date 2020–2026 |
| `*timestamp*` | Random datetime 2020–2026 |
| Anything else | `faker.word()` |

### Primary Key Handling

- Auto-increment primary keys are **skipped** (database handles them)
- UUID-typed primary keys get a `faker.uuid4()` value

## Supported Databases

| Database | Status | Driver | Port | Notes |
|----------|--------|--------|------|-------|
| **Kingbase** | Fully implemented | psycopg2 | 54321 (default) | Uses PostgreSQL protocol compatibility; queries `sys_tables` with `pg_tables` fallback |
| **MySQL** | Fully implemented | pymysql | 3306 (default) | Uses `pymysql` driver; `information_schema`-based metadata queries; `utf8mb4` support |

## Installation

### Prerequisites

- Python 3.12 or higher
- Operating system: Windows 10+, macOS 12+, or Linux with GTK

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/claude-code-db-plugin.git
cd claude-code-db-plugin

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### pip Editable Install

```bash
pip install -e .

# Launch via console entry point
db-plugin
```

### Dependencies

```
PySide6>=6.6          # Qt for Python (GUI framework)
psycopg2-binary>=2.9  # PostgreSQL/Kingbase driver
pymysql>=1.0          # MySQL driver
faker>=20.0           # Fake data generation
openpyxl>=3.1         # Excel file I/O
cryptography>=3.4     # Password encryption
pytest>=7.0           # Testing framework
```

## Usage Guide

### 1. Managing Database Connections

#### Create a Connection

1. Launch the application and click **Connection Management** on the toolbar (or **File → Connection Management**).
2. Click **New** to clear the form.
3. Fill in the connection details:
   - **Name**: A friendly name for this connection (e.g., "Production DB")
   - **Dialect**: Select the database type from the dropdown (`kingbase`, `mysql`)
   - **Host**: Database server hostname (default: `localhost`)
   - **Port**: Server port (Kingbase default: `54321`, MySQL default: `3306`)
   - **Username**: Database username
   - **Password**: Database password (masked input)
   - **Database**: Target database name
4. Click **Test Connection** to verify connectivity before saving.
5. Click **Save** to persist the connection.

Connections are stored in `~/.claude-code-db-plugin/connections.json` and survive application restarts.

#### Connect / Switch / Delete

- **Connect**: Select a saved connection from the list and click **Connect**. On success, the dialog closes and the status bar updates.
- **Switch**: Use **Connection Management** again to select a different saved connection.
- **Delete**: Select a connection and click **Delete**. Removes it from the config file.

### 2. Browsing Table Data

1. After connecting, the **Database Objects** panel on the left populates with tables and views.
2. **Double-click** any table name to load its data in the **Data Browser** tab.
3. Data loads in pages of 100 rows. Use **Prev Page** / **Next Page** to navigate.
4. The table view supports:
   - **Column sorting** — click column headers
   - **Alternating row colors** for readability
   - **Row count and page indicator** in the status area

### 4. Editing Data

1. In the Data Browser, click **编辑模式 (Edit Mode)** to enter editable state.
2. Click **新增行 (Add Row)** to insert a blank row, or modify existing cells directly.
3. **Primary Key editing**: PK columns are editable on new rows
   - If left empty, a unique PK value is auto-generated on save
   - If manually entered, conflicts are detected in real-time and rejected with a warning
4. Modified cells show a yellow background; new rows show a green background.
5. Available actions:
   - **Add Row** — adds a blank row, auto-focuses on the PK column
   - **Delete Row** — select rows or cells then click delete
   - **Save Changes** — writes local changes to the database (deletes → updates → inserts)
   - **Discard Changes** — reverts all local modifications
6. Click **只读模式 (Read Only)** to exit edit mode.

### 3. Executing SQL Queries

1. Switch to the **SQL Editor** tab.
2. Type your SQL in the text area. Multi-statement queries are supported.
3. Click **Execute** or press **Ctrl+Return**.
4. Results display in a sortable table below the editor.
5. The status area shows:
   - **Green text**: Success — row count affected
   - **Red text**: Error message from the database
   - **Execution time**: Milliseconds elapsed

All executed queries are automatically recorded in the query history (SQLite-backed).

### 5. Generating Fake Data

1. Ensure you are connected to a database.
2. Click **Tools → Fake Data Generator** or the toolbar button.
3. Select a target table from the dropdown (populated from the current connection).
4. Set the number of rows to generate (1–10,000).
5. **Advanced options**:
   - **Time Type**: Choose the date-time generation range (current time, 1 week ago, 1 month ago, 1 year ahead, etc. — 10 modes)
   - **Integer Mode**: Non-negative integers or allow negative
   - **Address File**: Specify a custom address data file (default: 4407 built-in Chinese addresses)
   - **Custom Rules**: Configure column name pattern to Faker method mappings
   - **Rule Files**: Configure per-column random value rules from local files
6. Click **Preview** to see up to 5 sample rows with generated values.
7. Click **Generate & Insert** to generate and insert all rows.
8. A summary dialog shows successful and failed insert counts.

The generator intelligently maps column names to realistic data (e.g., `email` columns get email addresses, `name` columns get person names). See the [Fake Data Generation](#fake-data-generation) section above for the full mapping.

### 6. Importing and Exporting Data

#### Export

1. Click the **Export** toolbar button.
2. Select the source table from the dropdown.
3. Choose the export format: **CSV**, **Excel**, or **JSON**.
4. Click **Select File** to pick a save location.
5. Click **Export**. Exports up to 10,000 rows.

- CSV files use UTF-8 with BOM encoding (`utf-8-sig`) for Excel compatibility.
- Excel files have a single sheet named "Query Result".
- JSON files use 2-space indentation with `default=str` for non-serializable types.

#### Import

1. Click the **Import** toolbar button.
2. Switch the mode to **Import** (if not already).
3. Choose the import format: **CSV** or **Excel** (JSON import is not yet supported).
4. Click **Select File** to pick the source file.
5. Enter the target table name in the **Target Table** field.
6. Click **Import**. The summary shows the number of successfully inserted records.

### 7. Query History

All SQL executions are automatically recorded with:
- The SQL text
- Connection name
- Timestamp
- Status (success/error)
- Execution time in milliseconds
- Favorite marking

History is stored in `~/.claude-code-db-plugin/history.db` (SQLite) and persists across sessions. The service supports:

- **List** — most recent 50 entries by default
- **Search** — fuzzy match on SQL text (`LIKE %keyword%`)
- **Toggle favorite** — mark/unmark entries
- **Delete** — remove individual entries

## Project Structure

```
claude-code-db-plugin/
├── src/
│   └── db_plugin/
│       ├── __init__.py
│       ├── main.py                      # Application entry: creates app + window
│       │
│       ├── core/
│       │   ├── __init__.py              # Exports: DatabaseConnection, QueryExecutor
│       │   ├── connection.py            # DatabaseConnection — lifecycle management
│       │   └── executor.py              # QueryExecutor — execute, execute_many, commit, rollback
│       │
│       ├── dialects/
│       │   ├── __init__.py              # Registry + get_dialect() factory
│       │   ├── dialect_base.py          # DialectBase — 12-method abstract interface
│       │   ├── kingbase.py              # KingbaseDialect — full implementation
│       │   └── mysql.py                 # MySQLDialect — scaffolded placeholder
│       │
│       ├── models/
│       │   ├── __init__.py              # All model exports
│       │   ├── config.py                # ConnectionConfig dataclass
│       │   ├── schema.py                # TableSchema, ColumnSchema, IndexSchema
│       │   ├── result.py                # QueryResult dataclass
│       │   └── history.py               # QueryHistoryEntry dataclass
│       │
│       └── services/
│           ├── __init__.py              # Exports: ConnectionManager, CRUDService
│           ├── connection_manager.py    # Multi-connection CRUD + persistence
│           ├── crud_service.py          # High-level CRUD with pagination
│           ├── fake_data_generator.py   # Schema-aware fake data + FIELD_NAME_RULES
│           ├── import_export.py         # CSV/Excel/JSON import and export
│           └── query_history.py         # SQLite-backed query history
│           │
│           └── gui/
│               ├── __init__.py
│               ├── app.py                   # create_application() — QApplication setup
│               ├── main_window.py           # MainWindow — menu, toolbar, tabs, dock
│               ├── widgets/
│               │   ├── __init__.py
│               │   ├── object_tree.py       # ObjectTreePanel — database object tree
│               │   ├── data_browser.py      # DataBrowserWidget + QueryResultModel
│               │   └── sql_editor.py        # SqlEditorWidget — SQL input + results
│               └── dialogs/
│                   ├── __init__.py
│                   ├── connection_dialog.py # ConnectionDialog — connection management UI
│                   ├── fake_data_dialog.py  # FakeDataDialog — generate + preview + insert
│                   └── import_export_dialog.py # ImportExportDialog — file I/O UI
│
├── tests/
│   ├── __init__.py
│   ├── test_models.py                 # Model dataclass construction tests
│   ├── test_dialects.py               # Abstract class + Kingbase + MySQL tests
│   ├── test_core.py                   # DatabaseConnection + QueryExecutor tests
│   └── test_services.py               # ConnectionManager + CRUD + FakeData + History tests
│
├── main.py                            # Root entry: adds src/ to path, calls db_plugin.main
├── setup.py                           # setuptools config with console_scripts entry point
├── requirements.txt                   # Runtime + test dependencies
├── README.md                          # This file (English)
├── README.zh.md                       # Chinese documentation
└── CLAUDE.md                          # Agent instructions
```

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
PYTHONPATH=src pytest tests/ -v

# Run a specific test file
PYTHONPATH=src pytest tests/test_models.py -v

# Run with coverage
PYTHONPATH=src pytest tests/ -v --cov=db_plugin --cov-report=term-missing
```

## Configuration & Storage

| File | Location | Purpose |
|------|----------|---------|
| `connections.json` | `~/.claude-code-db-plugin/connections.json` | Saved database connections (JSON array, passwords Fernet-encrypted) |
| `.key` | `~/.claude-code-db-plugin/.key` | Fernet encryption key (auto-generated, keep secure) |
| `history.db` | `~/.claude-code-db-plugin/history.db` | Query execution history (SQLite, `query_history` table) |

Both files are created automatically on first use. The `~/.claude-code-db-plugin/` directory is created if it does not exist.

## API Usage Examples

### Programmatic Connection and Query

```python
from db_plugin.models.config import ConnectionConfig
from db_plugin.core.connection import DatabaseConnection
from db_plugin.core.executor import QueryExecutor
from db_plugin.services.crud_service import CRUDService

# Create connection
config = ConnectionConfig(
    name="mydb",
    dialect_name="kingbase",
    host="localhost",
    port=54321,
    username="system",
    password="secret",
    database="testdb",
)
conn = DatabaseConnection(config)
conn.connect()

# Execute a query
executor = QueryExecutor(conn)
result = executor.execute("SELECT * FROM users WHERE id > %s", (10,))
print(f"Got {result.row_count} rows in {result.execution_time_ms:.0f}ms")
for row in result.rows:
    print(row)

# CRUD operations
crud = CRUDService(executor)
schema = crud.get_schema("users")
records = crud.read_records("users", where={"status": "active"}, limit=50)

# Cleanup
conn.close()
```

### Generating Fake Data Programmatically

```python
from db_plugin.services.fake_data_generator import FakeDataGenerator
from db_plugin.models.schema import TableSchema, ColumnSchema

table = TableSchema(
    name="employees",
    columns=[
        ColumnSchema(name="id", data_type="integer", is_primary_key=True),
        ColumnSchema(name="name", data_type="varchar"),
        ColumnSchema(name="email", data_type="varchar"),
        ColumnSchema(name="salary", data_type="numeric"),
        ColumnSchema(name="created_at", data_type="timestamp"),
    ],
    primary_keys=["id"],
)

generator = FakeDataGenerator()
records = generator.generate(table, count=10)
for r in records:
    print(r)
# {'name': 'John Smith', 'email': 'john@example.com', 'salary': 4523.12, ...}
```

### Export Query Results to Files

```python
from db_plugin.services.import_export import ImportExportService

service = ImportExportService(executor)

# First, get query result
result = executor.execute("SELECT * FROM users")

# Export to different formats
service.export_csv(result, "users.csv")
service.export_excel(result, "users.xlsx")
service.export_json(result, "users.json")
```

## Roadmap

- [ ] SQL editor syntax highlighting via QScintilla integration
- [ ] Additional dialects: PostgreSQL (native), Oracle, SQL Server
- [ ] Connection grouping and tenant labels for multi-tenant workflows
- [ ] Data visualization charts for query results
- [ ] ER diagram generation from table schema metadata
- [ ] Async query execution with `QThread` to prevent UI blocking on long-running queries
- [ ] JSON import support in `ImportExportDialog`

## Contributing

### Adding a New Dialect

1. Create `src/db_plugin/dialects/your_dialect.py`
2. Subclass `DialectBase` and implement all 12 abstract methods
3. Add to `DIALECT_REGISTRY` in `src/db_plugin/dialects/__init__.py`
4. Write tests in `tests/test_dialects.py`
5. Run `PYTHONPATH=src pytest tests/test_dialects.py -v` to verify

### Code Style

- Pure `dataclass` for all models — no business logic in the Models layer
- Services call Core, Core calls Dialects — never skip layers
- All SQL execution uses parameterized queries — never string concatenation for values
- Tests are layer-isolated: model tests need no database, dialect tests use placeholders

## License

MIT
