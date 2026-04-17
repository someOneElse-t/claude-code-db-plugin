# Claude Code DB Plugin — 数据库管理工具

基于 PySide6 的桌面数据库管理 GUI 工具，采用可插拔的方言架构，支持多数据库连接、增删改查、SQL 查询执行、假数据生成和数据导入导出。

[English Documentation](README.en.md)

## 目录

- [功能特性](#功能特性)
- [界面预览](#界面预览)
- [技术栈](#技术栈)
- [架构设计](#架构设计)
- [方言系统](#方言系统)
- [数据模型](#数据模型)
- [假数据生成](#假数据生成)
- [支持的数据库](#支持的数据库)
- [安装](#安装)
- [使用指南](#使用指南)
- [项目结构](#项目结构)
- [运行测试](#运行测试)
- [配置与存储](#配置与存储)
- [API 使用示例](#api-使用示例)
- [路线图](#路线图)
- [贡献](#贡献)
- [许可证](#许可证)

## 功能特性

- **多方言架构** — 插件式方言系统，具有明确的抽象接口。内置完整实现的 Kingbase（人大金仓）和 MySQL 占位实现。
- **连接管理** — 保存、加载、测试和切换多个数据库连接，配置持久化到 `~/.claude-code-db-plugin/connections.json`。
- **SQL 查询执行** — 编写和执行任意 SQL，支持参数化查询（防 SQL 注入）、执行计时、结果展示和自动历史记录。
- **CRUD 操作** — 完整的增删改查支持，自动解析主键和分页功能。
- **假数据生成** — 基于表结构的智能数据生成，20+ 字段名模式匹配（姓名、邮箱、电话、地址等），支持数据预览后插入。
- **数据导入导出** — CSV、Excel 和 JSON 格式导出；CSV 和 Excel 格式导入，自动列映射。
- **查询历史** — 基于 SQLite 的本地查询历史记录，支持搜索、收藏标记和执行元数据。
- **数据库对象树** — 左侧面板展示数据库对象（表、视图），支持右键菜单和双击浏览数据。

## 界面预览

```
┌─────────────────────────────────────────────────────────────────┐
│ 菜单栏  [文件] [编辑] [查询] [工具] [帮助]                        │
├─────────────────────────────────────────────────────────────────┤
│ 工具栏  [连接管理] [执行SQL] [假数据] [导入] [导出]                │
├──────────┬──────────────────────────────────────────────────────┤
│          │  ┌────────────────────────────────────┐              │
│ 数据库对 │  │  数据浏览   │   SQL 编辑器          │  (标签页)    │
│ 象       │  │                                    │              │
│ ├ 表     │  │  表名: users          [上一页][下一页]│              │
│ │ ├users │  │  ┌──────────────────────────────────┤│              │
│ │ ├orders│  │  │ id │ name  │ email        │ addr││              │
│ │ └roles │  │  │ 1  │ Alice │ a@test.com   │ BJ  ││              │
│ ├ 视图   │  │  │ 2  │ Bob   │ b@test.com   │ SH  ││              │
│          │  │  └──────────────────────────────────┤│              │
│          │  └────────────────────────────────────┘│              │
├──────────┴──────────────────────────────────────────────────────┤
│ 状态栏  [已连接: kingbase@localhost:54321/mydb] [就绪]            │
└─────────────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| GUI 界面 | PySide6 (Qt 6.6+) | 桌面应用框架，Fusion 风格 |
| 数据库驱动 | psycopg2-binary (2.9+) | 通过 PostgreSQL 协议连接 Kingbase |
| 假数据 | Faker (20.0+) | 真实测试数据生成 |
| Excel I/O | openpyxl (3.1+) | Excel 文件读写 |
| 测试 | pytest (7.0+) | 单元测试框架 |
| Python | 3.12+ | 语言运行时，PEP 695 类型注解 |

## 架构设计

### 分层架构图

```
┌─────────────────────────────────────────────────┐
│  GUI 界面层 (PySide6)                            │
│  MainWindow, ObjectTree, DataBrowser, SqlEditor │
│  ConnectionDialog, FakeDataDialog, ImportExport  │
│         │                                       │
│         ▼ (仅调用服务层)                         │
├─────────────────────────────────────────────────┤
│  Services 服务层                                 │
│  ConnectionManager  │  CRUDService              │
│  FakeDataGenerator  │  ImportExportService      │
│  QueryHistoryService                            │
│         │                                       │
│         ▼ (使用模型层，调用核心层 + 方言层)       │
├─────────────────────────────────────────────────┤
│  Models 模型层 (dataclasses)                     │
│  ConnectionConfig  │  TableSchema / ColumnSchema│
│  QueryResult       │  QueryHistoryEntry         │
│  IndexSchema                                    │
├──────────────┬──────────────────────────────────┤
│  Core 核心层 │  ← 依赖模型层 + 方言层            │
│  DatabaseConnection  │  QueryExecutor           │
├──────────────┴──────────────────────────────────┤
│  Dialects 方言层 (可插拔 SQL 实现)               │
│  DialectBase (ABC) → KingbaseDialect            │
│                     → MySQLDialect (占位)        │
└─────────────────────────────────────────────────┘
```

**依赖方向**: `GUI → Services → Models ← Core → Dialects`

GUI 仅与服务层交互。服务层使用模型和核心层。核心层桥接方言层。模型层零依赖。

### 层级职责

| 层级 | 关键类 | 职责 |
|------|--------|------|
| **GUI 界面** | `MainWindow`, `ObjectTreePanel`, `DataBrowserWidget`, `SqlEditorWidget`, `ConnectionDialog`, `FakeDataDialog`, `ImportExportDialog` | 所有 UI 组件，无数据库逻辑，委托给服务层。使用 `QTableView` + 自定义 `QAbstractTableModel` 展示结果。 |
| **Services 服务** | `ConnectionManager`, `CRUDService`, `FakeDataGenerator`, `ImportExportService`, `QueryHistoryService` | 业务逻辑：连接持久化、参数化 CRUD、智能数据生成、文件 I/O、基于 SQLite 的查询历史。 |
| **Models 模型** | `ConnectionConfig`, `TableSchema`, `ColumnSchema`, `IndexSchema`, `QueryResult`, `QueryHistoryEntry` | 纯 `dataclass` 定义，无数据库连接、无业务逻辑，全层共享。 |
| **Core 核心** | `DatabaseConnection`, `QueryExecutor` | 连接生命周期管理（连接/关闭/提交/回滚），参数化查询执行，支持 `execute_many`。 |
| **Dialects 方言** | `DialectBase`, `KingbaseDialect`, `MySQLDialect` | SQL 方言抽象：标识符引用、类型映射、元数据查询（表/列/主键/视图）、CRUD SQL 生成。 |

## 方言系统

### `DialectBase` 抽象接口

所有数据库方言必须实现以下 12 个方法：

```python
class DialectBase(ABC):
    name: str              # 方言标识，如 "kingbase"
    quote_char: str        # 标识符引号：Kingbase 用 "，MySQL 用 `

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

### 实现新方言

1. 继承 `DialectBase`
2. 设置 `name` 和 `quote_char` 类属性
3. 实现全部 12 个抽象方法
4. 在 `dialects/__init__.py` 的 `DIALECT_REGISTRY` 中注册

```python
from db_plugin.dialects.dialect_base import DialectBase

class PostgresDialect(DialectBase):
    name = "postgres"
    quote_char = '"'
    # ... 使用 psycopg2 或 asyncpg 实现方法
```

```python
# 在 dialects/__init__.py 中
DIALECT_REGISTRY = {
    "kingbase": KingbaseDialect,
    "mysql": MySQLDialect,
    "postgres": PostgresDialect,  # 添加新方言
}
```

### Kingbase 方言细节

- **驱动**: `psycopg2`，使用 `RealDictCursor` 实现字典形式的行访问
- **协议**: Kingbase 兼容 PostgreSQL 协议，标准 PostgreSQL 连接参数即可
- **元数据查询**: 优先查询 `sys_tables`（Kingbase 专用目录），失败则回退到 `pg_tables`
- **SQL 注入防护**: 所有 CRUD 操作均使用 `%s` 参数化查询
- **事务处理**: `autocommit = False`，成功提交，失败回滚
- **标识符引用**: 使用双引号 `"` 引用所有表名和列名

### MySQL 方言状态

当前为占位实现 — 类结构已定义，`name = "mysql"`，引号为反引号 `` ` ``，但所有方法抛出 `NotImplementedError`。测试套件验证了占位行为。

## 数据模型

### `ConnectionConfig` — 连接配置

```python
@dataclass
class ConnectionConfig:
    name: str                    # 连接名称（用户友好名称）
    dialect_name: str            # 方言名称，如 "kingbase"、"mysql"
    host: str                    # 主机地址
    port: int                    # 端口号
    username: str                # 用户名
    password: str                # 密码
    database: str                # 目标数据库名称
    extra_params: dict           # 额外驱动参数
```

### `TableSchema` / `ColumnSchema` / `IndexSchema` — 表结构定义

```python
@dataclass
class ColumnSchema:
    name: str                    # 列名
    data_type: str               # 数据库类型
    is_nullable: bool = True     # 是否可空
    default_value: str | None    # 默认值
    is_primary_key: bool = False # 是否主键
    comment: str = ""            # 列注释

@dataclass
class IndexSchema:
    name: str                    # 索引名称
    columns: list[str]           # 索引列
    is_unique: bool = False      # 是否唯一索引
    is_primary: bool = False     # 是否主键索引

@dataclass
class TableSchema:
    name: str                    # 表名
    columns: list[ColumnSchema]  # 所有列
    primary_keys: list[str]      # 主键列
    indexes: list[IndexSchema]   # 表索引，默认为 []
```

### `QueryResult` — 查询执行结果

```python
@dataclass
class QueryResult:
    columns: list[str]           # 列名列表（来自 cursor.description）
    rows: list[dict]             # 每行为字典形式 {列名: 值}
    row_count: int               # 影响行数（cursor.rowcount）
    execution_time_ms: float     # 执行耗时（毫秒）
    error_message: str | None    # 错误信息（成功时为 None）
```

### `QueryHistoryEntry` — 历史记录

```python
@dataclass
class QueryHistoryEntry:
    id: int                      # 自增 ID
    sql: str                     # SQL 文本
    connection_name: str         # 连接名称
    timestamp: datetime          # 执行时间
    status: str                  # 状态："success"（成功）| "error"（失败）
    execution_time_ms: float     # 执行耗时（毫秒）
    is_favorite: bool = False    # 收藏标记
```

## 假数据生成

`FakeDataGenerator` 采用两层匹配策略：

### 第一层：字段名模式匹配

20+ 内置字段名模式，将列名映射到 Faker 方法：

| 列名包含 | 生成值 | Faker 方法 |
|---------|--------|-----------|
| `name` | 人名 | `faker.name()` |
| `username` | 用户名 | `faker.user_name()` |
| `email` | 邮箱地址 | `faker.email()` |
| `phone`、`mobile` | 电话号码 | `faker.phone_number()` |
| `address` | 街道地址 | `faker.address()` |
| `city` | 城市名 | `faker.city()` |
| `country` | 国家名 | `faker.country()` |
| `zip`、`postal_code` | 邮政编码 | `faker.zipcode()` |
| `company` | 公司名 | `faker.company()` |
| `url` | 网址 | `faker.url()` |
| `ip` | IPv4 地址 | `faker.ipv4()` |
| `title` | 句子 | `faker.sentence()` |
| `description`、`comment` | 段落文本 | `faker.text()` |
| `password` | 密码字符串 | `faker.password()` |
| `token`、`uuid` | UUID v4 | `faker.uuid4()` |
| `created_at`、`updated_at` | 日期时间 | `faker.date_time()` |
| `date` | 日期（2020–2026） | `faker.date()` |
| `birthday` | 生日 | `faker.date_of_birth()` |

### 第二层：数据类型回退

当字段名无匹配时，根据数据类型生成：

| 数据类型 | 生成值 |
|---------|--------|
| `integer`、`bigint`、`smallint`、`serial` | 随机整数 1–99,999 |
| `real`、`double precision`、`numeric`、`decimal`、`float` | 随机浮点数 0.0–9999.99 |
| `boolean`、`bool` | 随机布尔值 |
| `date` | 随机日期（2020–2026） |
| `*timestamp*` | 随机日期时间（2020–2026） |
| 其他类型 | `faker.word()` 随机单词 |

### 主键处理

- 自增主键**自动跳过**（由数据库处理）
- UUID 类型主键使用 `faker.uuid4()` 生成值

## 支持的数据库

| 数据库 | 状态 | 驱动 | 默认端口 | 说明 |
|--------|------|------|---------|------|
| **Kingbase**（人大金仓） | 已完整实现 | psycopg2 | 54321 | 使用 PostgreSQL 协议兼容；查询 `sys_tables` 并回退 `pg_tables` |
| **MySQL** | 占位 | — | 3306 | 类结构已搭建，使用反引号 `` ` `` ；所有方法抛出 `NotImplementedError` |

## 安装

### 前置要求

- Python 3.12 或更高版本
- 操作系统：Windows 10+、macOS 12+ 或 Linux（带 GTK）

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/your-org/claude-code-db-plugin.git
cd claude-code-db-plugin

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

### pip 可编辑安装

```bash
pip install -e .

# 通过命令行入口启动
db-plugin
```

### 依赖列表

```
PySide6>=6.6          # Qt for Python（GUI 框架）
psycopg2-binary>=2.9  # PostgreSQL/Kingbase 驱动
faker>=20.0           # 假数据生成
openpyxl>=3.1         # Excel 文件读写
pytest>=7.0           # 测试框架
```

## 使用指南

### 1. 管理数据库连接

#### 创建连接

1. 启动应用，点击工具栏 **连接管理**（或 **文件 → 连接管理**）。
2. 点击 **新建** 清空表单。
3. 填写连接信息：
   - **名称**: 连接的友好名称（如"生产数据库"）
   - **方言**: 从下拉列表选择数据库类型（`kingbase`、`mysql`）
   - **主机**: 数据库服务器地址（默认 `localhost`）
   - **端口**: 服务器端口（Kingbase 默认 `54321`，MySQL 默认 `3306`）
   - **用户名**: 数据库用户名
   - **密码**: 数据库密码（掩码输入）
   - **数据库**: 目标数据库名称
4. 点击 **测试连接** 验证连通性。
5. 点击 **保存** 持久化连接配置。

连接配置保存在 `~/.claude-code-db-plugin/connections.json`，重启后仍然有效。

#### 连接 / 切换 / 删除

- **连接**: 从列表中选择已保存的连接，点击 **连接**。成功后对话框关闭，状态栏更新。
- **切换**: 再次打开 **连接管理**，选择其他已保存连接。
- **删除**: 选择一个连接，点击 **删除**，从配置文件中移除。

### 2. 浏览表数据

1. 连接成功后，左侧 **数据库对象** 面板自动加载表和视图。
2. **双击** 任意表名，在 **数据浏览** 标签页中加载数据。
3. 数据按每页 100 行分页加载，使用 **上一页** / **下一页** 切换。
4. 表格视图支持：
   - **列排序** — 点击列头排序
   - **交替行颜色** 便于阅读
   - **行数和页码指示**

### 3. 执行 SQL 查询

1. 切换到 **SQL 编辑器** 标签页。
2. 在文本区域输入 SQL，支持多语句查询。
3. 点击 **执行** 或按 **Ctrl+Return**。
4. 结果在编辑器下方的可排序表格中展示。
5. 状态区域显示：
   - **绿色文字**: 成功 — 影响行数
   - **红色文字**: 数据库错误信息
   - **执行耗时**: 毫秒数

所有执行的查询自动记录到查询历史（基于 SQLite）。

### 4. 生成假数据

1. 确保已连接数据库。
2. 点击 **工具 → 假数据生成** 或工具栏 **假数据** 按钮。
3. 从下拉列表选择目标表（自动从当前连接加载）。
4. 设置生成条数（1–10,000）。
5. 点击 **预览** 查看最多 5 条样例数据。
6. 点击 **生成并插入** 生成并插入全部数据。
7. 弹窗显示成功和失败的插入数量。

生成器智能匹配列名到真实数据（如 `email` 列生成邮箱地址，`name` 列生成人名）。详见上方 [假数据生成](#假数据生成) 章节的完整映射表。

### 5. 导入导出数据

#### 导出

1. 点击工具栏 **导出** 按钮。
2. 从下拉列表选择源表。
3. 选择导出格式：**CSV**、**Excel** 或 **JSON**。
4. 点击 **选择文件** 选择保存位置。
5. 点击 **导出**，最多导出 10,000 行。

- CSV 文件使用 UTF-8 BOM 编码（`utf-8-sig`），兼容 Excel。
- Excel 文件包含一个名为 "Query Result" 的工作表。
- JSON 文件使用 2 空格缩进，非序列化类型使用 `default=str`。

#### 导入

1. 点击工具栏 **导入** 按钮。
2. 选择导入格式：**CSV** 或 **Excel**（暂不支持 JSON 导入）。
3. 点击 **选择文件** 选择源文件。
4. 在 **目标表** 字段中输入表名。
5. 点击 **导入**，显示成功插入的记录数。

### 6. 查询历史

所有 SQL 执行自动记录：
- SQL 文本
- 连接名称
- 时间戳
- 状态（成功/失败）
- 执行耗时（毫秒）
- 收藏标记

历史存储在 `~/.claude-code-db-plugin/history.db`（SQLite），跨会话持久化。服务支持：

- **列表** — 默认最近 50 条
- **搜索** — SQL 文本模糊匹配（`LIKE %keyword%`）
- **切换收藏** — 标记/取消标记
- **删除** — 删除单条记录

## 项目结构

```
claude-code-db-plugin/
├── src/
│   └── db_plugin/
│       ├── __init__.py
│       ├── main.py                      # 应用入口：创建应用 + 主窗口
│       │
│       ├── core/                        # 核心层
│       │   ├── __init__.py              # 导出: DatabaseConnection, QueryExecutor
│       │   ├── connection.py            # DatabaseConnection — 连接生命周期管理
│       │   └── executor.py              # QueryExecutor — 执行查询、批量执行、提交、回滚
│       │
│       ├── dialects/                    # 方言层
│       │   ├── __init__.py              # 方言注册表 + get_dialect() 工厂函数
│       │   ├── dialect_base.py          # DialectBase — 12 方法抽象接口
│       │   ├── kingbase.py              # KingbaseDialect — 完整实现
│       │   └── mysql.py                 # MySQLDialect — 占位实现
│       │
│       ├── models/                      # 模型层
│       │   ├── __init__.py              # 所有模型导出
│       │   ├── config.py                # ConnectionConfig 连接配置
│       │   ├── schema.py                # TableSchema, ColumnSchema, IndexSchema 表结构定义
│       │   ├── result.py                # QueryResult 查询结果
│       │   └── history.py               # QueryHistoryEntry 查询历史
│       │
│       └── services/                    # 服务层
│           ├── __init__.py              # 导出: ConnectionManager, CRUDService
│           ├── connection_manager.py    # 多连接管理 + 持久化
│           ├── crud_service.py          # 高级 CRUD 操作 + 分页
│           ├── fake_data_generator.py   # 智能假数据生成 + 字段名规则
│           ├── import_export.py         # CSV/Excel/JSON 导入导出
│           └── query_history.py         # SQLite 查询历史
│           │
│           └── gui/                     # GUI 界面层
│               ├── __init__.py
│               ├── app.py                   # create_application() — 应用初始化
│               ├── main_window.py           # MainWindow — 主窗口：菜单、工具栏、标签页、停靠面板
│               ├── widgets/
│               │   ├── __init__.py
│               │   ├── object_tree.py       # ObjectTreePanel — 数据库对象树
│               │   ├── data_browser.py      # DataBrowserWidget + QueryResultModel — 数据浏览表格
│               │   └── sql_editor.py        # SqlEditorWidget — SQL 编辑器 + 结果展示
│               └── dialogs/
│                   ├── __init__.py
│                   ├── connection_dialog.py # ConnectionDialog — 连接管理对话框
│                   ├── fake_data_dialog.py  # FakeDataDialog — 假数据生成对话框
│                   └── import_export_dialog.py # ImportExportDialog — 导入导出对话框
│
├── tests/                           # 测试套件
│   ├── __init__.py
│   ├── test_models.py               # 模型测试
│   ├── test_dialects.py             # 方言测试
│   ├── test_core.py                 # 核心层测试
│   └── test_services.py             # 服务层测试
│
├── main.py                          # 根入口：将 src/ 加入路径，调用 db_plugin.main
├── setup.py                         # setuptools 配置，含 console_scripts 入口
├── requirements.txt                 # 运行时 + 测试依赖
├── README.md                        # 本文档（中文）
├── README.en.md                     # 英文文档
└── CLAUDE.md                        # Agent 指令
```

## 运行测试

```bash
# 安装测试依赖
pip install -r requirements.txt

# 运行全部测试
PYTHONPATH=src pytest tests/ -v

# 运行单个测试文件
PYTHONPATH=src pytest tests/test_models.py -v

# 带覆盖率运行
PYTHONPATH=src pytest tests/ -v --cov=db_plugin --cov-report=term-missing
```

## 配置与存储

| 文件 | 位置 | 用途 |
|------|------|------|
| `connections.json` | `~/.claude-code-db-plugin/connections.json` | 保存的数据库连接配置（JSON 数组） |
| `history.db` | `~/.claude-code-db-plugin/history.db` | 查询执行历史（SQLite，`query_history` 表） |

两个文件均在首次使用时自动创建，`~/.claude-code-db-plugin/` 目录也会自动创建。

## API 使用示例

### 编程方式连接与查询

```python
from db_plugin.models.config import ConnectionConfig
from db_plugin.core.connection import DatabaseConnection
from db_plugin.core.executor import QueryExecutor
from db_plugin.services.crud_service import CRUDService

# 创建连接
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

# 执行查询
executor = QueryExecutor(conn)
result = executor.execute("SELECT * FROM users WHERE id > %s", (10,))
print(f"获取 {result.row_count} 行数据，耗时 {result.execution_time_ms:.0f}ms")
for row in result.rows:
    print(row)

# CRUD 操作
crud = CRUDService(executor)
schema = crud.get_schema("users")
records = crud.read_records("users", where={"status": "active"}, limit=50)

# 清理
conn.close()
```

### 编程方式生成假数据

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

### 导出查询结果到文件

```python
from db_plugin.services.import_export import ImportExportService

service = ImportExportService(executor)

# 先获取查询结果
result = executor.execute("SELECT * FROM users")

# 导出到不同格式
service.export_csv(result, "users.csv")
service.export_excel(result, "users.xlsx")
service.export_json(result, "users.json")
```

## 路线图

- [ ] 完成 `MySQLDialect` 完整实现（使用 `pymysql` 或 `mysql-connector-python`）
- [ ] SQL 编辑器语法高亮（集成 QScintilla）
- [ ] 更多方言：原生 PostgreSQL、Oracle、SQL Server
- [ ] 连接分组和租户标签，支持多租户工作流
- [ ] 查询结果数据可视化图表
- [ ] 基于表结构元数据的 ER 图生成
- [ ] 异步查询执行（`QThread`），避免长查询阻塞 UI
- [ ] `ImportExportDialog` 中支持 JSON 导入

## 贡献

### 添加新方言

1. 创建 `src/db_plugin/dialects/your_dialect.py`
2. 继承 `DialectBase` 并实现全部 12 个抽象方法
3. 在 `src/db_plugin/dialects/__init__.py` 的注册表中添加新方言
4. 在 `tests/test_dialects.py` 中编写测试
5. 运行 `PYTHONPATH=src pytest tests/test_dialects.py -v` 验证

### 代码规范

- 所有模型使用纯 `dataclass` — 模型层不包含业务逻辑
- 服务层调用核心层，核心层调用方言层 — 不跨层调用
- 所有 SQL 执行使用参数化查询 — 绝不拼接值字符串
- 测试分层隔离：模型测试无需数据库，方言测试使用占位

## 许可证

MIT
