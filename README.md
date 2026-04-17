# Claude Code DB Plugin / 数据库管理插件

A desktop database management GUI tool built with PySide6, featuring a pluggable dialect architecture.
基于 PySide6 的桌面数据库管理 GUI 工具，采用可插拔的方言架构。

---

## Documentation / 文档

- [English Documentation](README.en.md)
- [中文文档](README.zh.md)

---

## Quick Start / 快速开始

```bash
git clone https://github.com/your-org/claude-code-db-plugin.git
cd claude-code-db-plugin
pip install -r requirements.txt
python main.py
```

## Features / 功能特性

- Multi-dialect architecture / 多方言架构
- Connection management / 连接管理
- SQL query execution / SQL 查询执行
- CRUD operations / 增删改查操作
- Fake data generation / 假数据生成
- Data import/export (CSV, Excel, JSON) / 数据导入导出
- Query history / 查询历史

## Tech Stack / 技术栈

| Layer | Technology |
|-------|------------|
| GUI | PySide6 (Qt 6.6+) |
| Database driver | psycopg2-binary (2.9+) |
| Fake data | Faker (20.0+) |
| Excel I/O | openpyxl (3.1+) |
| Testing | pytest (7.0+) |
| Python | 3.12+ |

## Supported Databases / 支持的数据库

| Database | Status | Driver |
|----------|--------|--------|
| **Kingbase** (人大金仓) | Fully implemented / 已实现 | psycopg2 |
| **MySQL** | Placeholder / 占位 | — |

## License / 许可证

MIT
