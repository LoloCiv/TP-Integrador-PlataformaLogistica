from pydantic_settings import BaseSettings, SettingsConfigDict


# Lee la configuración de las variables de entorno / .env
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "db"
    postgres_port: int = 5432

    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str
    jwt_expira_minutos: int = 60
    jwt_algoritmo: str = "HS256"

    cors_origins: str = "http://localhost:3000"

    log_level: str = "INFO"

    # Arma la URL de conexión a Postgres con los datos de arriba
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


# Instancia única que importa el resto del código
settings = Settings()
