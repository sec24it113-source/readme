import os
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

# Load environment variables from .env file
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

def get_database_uri():
    """
    Get and normalize database URI.
    Supports PostgreSQL (production & local) with psycopg3 driver.
    """
    uri = os.getenv("DATABASE_URL")
    if not uri:
        # Default production postgres URI or local postgres
        uri = os.getenv("POSTGRES_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/event_ticket_db")
    
    # Render and Heroku use 'postgres://' which SQLAlchemy 1.4+ / 2.0+ deprecated in favor of 'postgresql://'
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql+psycopg://", 1)
    elif uri.startswith("postgresql://") and "+psycopg" not in uri:
        uri = uri.replace("postgresql://", "postgresql+psycopg://", 1)
        
    return uri


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-random-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", 300))
    
    # Celery configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_TIMEZONE = "UTC"
    CELERY_ENABLE_UTC = True
    
    # Reservation configuration (10 minutes hold)
    RESERVATION_HOLD_SECONDS = int(os.getenv("RESERVATION_HOLD_SECONDS", 600))
    
    # Session cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    # WTForms CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = get_database_uri()


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_TEST_URL", "sqlite:///:memory:")
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False, "timeout": 15},
    } if "sqlite" in os.getenv("DATABASE_TEST_URL", "sqlite:///:memory:") else {
        "pool_pre_ping": True,
    }
    RESERVATION_HOLD_SECONDS = int(os.getenv("TEST_RESERVATION_HOLD_SECONDS", 600))
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "cache+memory://"


class ProductionConfig(Config):
    """Production configuration (e.g. on Render)."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
