from dataclasses import dataclass


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
    indexes: list[IndexSchema] = None

    def __post_init__(self):
        if self.indexes is None:
            self.indexes = []
