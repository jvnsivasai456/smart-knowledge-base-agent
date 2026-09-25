import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Server Config
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Paths Config
    data_dir: str = "./data"
    upload_dir: str = "./data/uploads"
    chroma_db_dir: str = "./data/chroma_db"
    metadata_db_path: str = "./data/metadata.sqlite"
    
    # Embedding Model Config
    embedding_model_name: str = "all-MiniLM-L6-v2"
    
    # Scheduler Config
    scheduler_interval_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def create_directories(self):
        """Ensure all required directories exist."""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.chroma_db_dir, exist_ok=True)

# Global settings instance
settings = Settings()
