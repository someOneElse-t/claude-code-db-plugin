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
