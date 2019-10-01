import os

base_dir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    """
    Base application configuration
    """

    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY", "houdsfhoisd")
    NYLAS_OAUTH_CLIENT_ID = os.getenv("NYLAS_OAUTH_CLIENT_ID", "")
    NYLAS_OAUTH_CLIENT_SECRET = os.getenv("NYLAS_OAUTH_CLIENT_SECRET", "")


class DevelopmentConfig(BaseConfig):
    """
    Development application configuration
    """

    DEBUG = True


class TestingConfig(BaseConfig):
    """
    Testing application configuration
    """

    DEBUG = True
    TESTING = True


class ProductionConfig(BaseConfig):
    """
    Production application configuration
    """

    DEBUG = False
