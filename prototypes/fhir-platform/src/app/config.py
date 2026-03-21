from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # HAPI FHIR
    fhir_base_url: str = "http://localhost:8080/fhir"

    # OpenSearch
    opensearch_endpoint: str = "http://localhost:9200"
    opensearch_index: str = "patients"

    # Import tracking DB (SQLite locally)
    database_url: str = "sqlite:///./import_tracking.db"

    # Local Synthea bundles directory
    synthea_bundles_dir: str = "./data/synthea_bundles"

    log_level: str = "INFO"


settings = Settings()
