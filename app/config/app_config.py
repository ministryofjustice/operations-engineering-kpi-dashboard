import os
from types import SimpleNamespace


def __get_env_var(name: str) -> str | None:
    return os.getenv(name)


def __get_env_var_as_boolean(name: str) -> bool | None:
    value = __get_env_var(name)

    if value is None:
        return False

    if value.lower() == "true":
        return True

    return False


app_config = SimpleNamespace(
    api_key=__get_env_var("API_KEY"),
    auth0=SimpleNamespace(
        domain=__get_env_var("AUTH0_DOMAIN"),
        client_id=__get_env_var("AUTH0_CLIENT_ID"),
        client_secret=__get_env_var("AUTH0_CLIENT_SECRET"),
    ),
    logging_level=__get_env_var("LOGGING_LEVEL"),
    postgres=SimpleNamespace(
        user=__get_env_var("POSTGRES_USER"),
        password=__get_env_var("POSTGRES_PASSWORD"),
        db=__get_env_var("POSTGRES_DB"),
        host=__get_env_var("POSTGRES_HOST"),
        port=__get_env_var("POSTGRES_PORT"),
    ),
    sentry=SimpleNamespace(
        dsn_key=__get_env_var("SENTRY_DSN_KEY"), environment=__get_env_var("SENTRY_ENV")
    ),
)
