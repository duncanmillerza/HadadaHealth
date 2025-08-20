"""
Configuration management for HadadaHealth application
"""
import os
import secrets
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        # Load environment variables from .env file in development
        load_dotenv()
        self._validate_required_config()
    
    @property
    def session_secret_key(self) -> str:
        """Get session secret key from environment"""
        key = os.getenv("SESSION_SECRET_KEY")
        if not key:
            raise ValueError(
                "SESSION_SECRET_KEY environment variable is required. "
                "Generate one using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Validate key length for security
        if len(key) < 32:
            raise ValueError(
                "SESSION_SECRET_KEY must be at least 32 characters long for security. "
                "Generate a new one using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        return key
    
    @property
    def database_path(self) -> str:
        """Get database path from environment or default"""
        return os.getenv("DATABASE_PATH", "data/bookings.db")
    
    @property
    def environment(self) -> str:
        """Get current environment (development, staging, production)"""
        return os.getenv("ENVIRONMENT", "development")
    
    @property
    def debug_mode(self) -> bool:
        """Get debug mode setting"""
        return os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
    
    @property
    def openrouter_api_key(self) -> Optional[str]:
        """Get OpenRouter API key from environment"""
        return os.getenv("OPENROUTER_API_KEY")
    
    def _validate_required_config(self):
        """Validate that all required configuration is present"""
        try:
            # This will raise ValueError if missing or invalid
            self.session_secret_key
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            print("🔧 To fix this:")
            print("1. Create a .env file in the project root")
            print("2. Add: SESSION_SECRET_KEY=<your-generated-key>")
            print("3. Generate a key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'")
            raise
    
    def generate_new_secret_key(self) -> str:
        """Generate a new cryptographically secure secret key"""
        return secrets.token_urlsafe(32)
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def get_session_config(self) -> dict:
        """Get secure session configuration"""
        base_config = {
            "secret_key": self.session_secret_key,
        }
        
        # Add production-specific security settings
        if self.is_production():
            base_config.update({
                "https_only": True,
                "same_site": "strict",
            })
        
        return base_config


# Global configuration instance
config = Config()


def validate_security_config():
    """Validate security configuration at startup"""
    print("🔐 Validating security configuration...")
    
    try:
        # Test session key
        key = config.session_secret_key
        print(f"✅ Session secret key loaded (length: {len(key)} characters)")
        
        # Validate key strength
        if len(key) >= 32:
            print("✅ Session key meets minimum security requirements")
        else:
            print(f"⚠️  Warning: Session key is only {len(key)} characters (recommend 32+)")
        
        # Environment check
        env = config.environment
        print(f"🌍 Environment: {env}")
        
        if config.is_production():
            print("🔒 Production mode: Enhanced security settings active")
        else:
            print("🛠️  Development mode: Standard security settings")
        
        return True
        
    except Exception as e:
        print(f"❌ Security configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    # CLI utility for generating keys
    print("🔑 HadadaHealth Configuration Utility")
    print("="*50)
    
    # Generate a new secret key
    new_key = config.generate_new_secret_key()
    print(f"Generated secure secret key: {new_key}")
    print("\nAdd this to your .env file:")
    print(f"SESSION_SECRET_KEY={new_key}")