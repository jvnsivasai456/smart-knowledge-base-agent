from src.config import settings

def test_config():
    print("Testing config loading...")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Upload Dir: {settings.upload_dir}")
    print(f"Embedding Model: {settings.embedding_model_name}")
    print("Config loaded successfully!")
    
    print("\nTesting directory creation...")
    settings.create_directories()
    print("Directories created/verified successfully!")

if __name__ == "__main__":
    test_config()
