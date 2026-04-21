# Claude Code DB Plugin / 数据库管理插件

A desktop database management GUI tool built with PySide6, featuring a pluggable dialect architecture.
基于 PySide6 的桌面数据库管理 GUI 工具，采用可插拔的方言架构。

## Quick Start / 快速开始

```bash
git clone https://github.com/your-org/claude-code-db-plugin.git
cd claude-code-db-plugin
pip install -e ".[dev]"
python main.py
```

## Features / 功能特性

- **Multi-dialect architecture** / 多方言架构 — plugin discovery via `importlib.metadata.entry_points`
- **Async query execution** / 异步查询执行 — non-blocking SQL execution with cancel support via `QThread`
- **i18n internationalization** / 国际化 — built-in Chinese (zh_CN) and English (en_US) translations
- **SQL syntax highlighting** / SQL 语法高亮 — keywords, functions, strings, comments, numbers
- **Dark/Light theme toggle** / 明暗主题切换 — persistent theme preference
- **Connection management** / 连接管理 — encrypted password storage via Fernet
- **SQL editor** / SQL 编辑器 — syntax highlighting, execution history with search and favorites
- **Data browser** / 数据浏览 — paginated table view with inline editing, add/delete rows
- **CRUD operations** / 增删改查操作 — update, insert, delete with PK conflict detection
- **Fake data generation** / 假数据生成 — smart column-name-based values via Faker, configurable rules
- **Data import/export** / 数据导入导出 — CSV, Excel, JSON formats
- **Query history** / 查询历史 — searchable, favoritable execution log

## Tech Stack / 技术栈

| Layer | Technology |
|-------|------------|
| GUI | PySide6 (Qt 6.6+) |
| Database drivers | psycopg2-binary, pymysql |
| Fake data | Faker (20.0+) |
| Excel I/O | openpyxl (3.1+) |
| Encryption | cryptography (3.4+) |
| Testing | pytest (7.0+) + pytest-qt, pytest-cov |
| Python | 3.12+ |

## Supported Databases / 支持的数据库

| Database | Status / 状态 | Driver |
|----------|--------|--------|
| **Kingbase** (人大金仓) | Fully implemented / 已实现 | psycopg2 |
| **MySQL** | Fully implemented / 已实现 | pymysql |

## Architecture / 架构

```
src/db_plugin/
  core/        — DatabaseConnection, QueryExecutor, QueryWorker
  dialects/    — DialectBase, KingbaseDialect, MySQLDialect (pluggable)
  models/      — dataclasses: ConnectionConfig, TableSchema, QueryResult, etc.
  services/    — ConnectionManager, CRUDService, FakeDataGenerator, ImportExportService
  gui/
    app.py, main_window.py, style.py
    dialogs/   — connection, fake data, import/export, history
    widgets/   — object tree, data browser, SQL editor (with highlighter)
    i18n.py    — translation engine with JSON fallback
  data/
    locales/   — zh_CN.json, en_US.json
    addresses.json
```

## License / 许可证

MIT
