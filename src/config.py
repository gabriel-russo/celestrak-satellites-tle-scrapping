from dynaconf import Dynaconf, LazySettings


def read_config() -> LazySettings:
    return Dynaconf(
        envvar_prefix="DYNACONF",
        settings_files=["settings.toml", ".secrets.toml"],
        environments=False,
    )
