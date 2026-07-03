from app.providers.divar import DivarProvider
from app.providers.hamrah_mechanic import HamrahMechanicProvider
from app.providers.iranfile import IranFileProvider
from app.providers.kilid import KilidProvider
from app.providers.sheypoor import SheypoorProvider


def build_providers(city_ids: dict[str, str]):
    return [
        DivarProvider(city_ids=city_ids),
        SheypoorProvider(),
        IranFileProvider(),
        KilidProvider(),
        HamrahMechanicProvider(),
    ]


def close_providers(providers: list[object]) -> None:
    for provider in providers:
        close = getattr(provider, "close", None)
        if close:
            close()
