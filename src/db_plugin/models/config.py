from dataclasses import dataclass, field


@dataclass
class ConnectionConfig:
    name: str
    dialect_name: str
    host: str
    port: int
    username: str
    password: str
    database: str
    extra_params: dict = field(default_factory=dict)


TIME_TYPE_LABELS = {
    0: "当前时间",
    1: "一周前 ~ 现在",
    2: "一个月前 ~ 现在",
    3: "一年前 ~ 现在",
    4: "现在 ~ 一周后",
    5: "现在 ~ 一个月后",
    6: "现在 ~ 一年后",
    7: "一周前 ~ 一周后",
    8: "一月前 ~ 一月后",
    9: "一年前 ~ 一年后",
}

INT_MODE_LABELS = {
    0: "非负整数",
    1: "允许负数",
}


@dataclass
class FakeDataConfig:
    """Configuration for fake data generation."""
    time_type: int = 0
    int_mode: int = 0
    address_file: str = ""
    extra_rules: dict = field(default_factory=dict)  # {pattern: faker_method}
