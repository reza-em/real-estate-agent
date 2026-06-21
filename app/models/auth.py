from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthUser:
    id: str
    username: str
    display_name: str
