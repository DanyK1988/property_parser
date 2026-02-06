from environs import Env
from pathlib import Path


def configure_db():
    env = Env()
    project_dir = Path(__file__).resolve().parent.parent
    env_file = project_dir / ".env"

    env.read_env(env_file)

    return {
        "user": env.str("POSTGRES_USER"),
        "password": env.str("POSTGRES_PASSWORD"),
        "db": env.str("POSTGRES_DB"),
        "host": env.str("POSTGRES_HOST"),
        "port": env.str("POSTGRES_PORT")
    }


def get_connection_string():
    config = configure_db()
    return f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}"

