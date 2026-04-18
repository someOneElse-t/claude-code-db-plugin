from setuptools import setup, find_packages

setup(
    name="claude-code-db-plugin",
    version="0.1.0",
    description="A database management GUI tool with multi-dialect support",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.12",
    install_requires=[
        "PySide6>=6.6",
        "psycopg2-binary>=2.9",
        "faker>=20.0",
        "openpyxl>=3.1",
    ],
    entry_points={
        "console_scripts": [
            "db-plugin=db_plugin.main:main",
        ],
    },
)
