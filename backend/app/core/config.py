from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ACRIP - Agentic Construction Risk Intelligence Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./acrip_dev.db"

    # JWT
    JWT_SECRET_KEY: str = "acrip-dev-secret-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Demo passwords
    DEMO_ADMIN_PASSWORD: str = "Admin@123"
    DEMO_MANAGER_PASSWORD: str = "Manager@123"
    DEMO_SITE_MANAGER_PASSWORD: str = "SiteManager@123"
    DEMO_SAFETY_PASSWORD: str = "Safety@123"
    DEMO_VIEWER_PASSWORD: str = "Viewer@123"

    # PPE Computer Vision Settings
    PPE_CONFIDENCE_THRESHOLD: float = 0.65
    PPE_UPLOAD_DIR: str = "uploads/ppe"
    PPE_MAX_FILE_SIZE_MB: int = 15
    PPE_ALLOWED_EXTENSIONS: str = "jpg,jpeg,png"

    # Worker Safety Monitoring Settings (Phase 2.3)
    MONITORING_TIME_IN_ZONE_THRESHOLD_MINUTES: int = 45
    MONITORING_MAX_ZONE_WORKERS: int = 3
    MONITORING_SAFE_EQUIPMENT_DISTANCE_METERS: float = 10.0

    # Safety Alert System Settings (Phase 2.4)
    ALERT_CRITICAL_TIMEOUT_MINUTES: int = 15
    ALERT_HIGH_TIMEOUT_MINUTES: int = 30
    ALERT_AUTO_ESCALATE_ENABLED: bool = True

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def allowed_ppe_extensions_list(self) -> List[str]:
        return [e.strip().lower() for e in self.PPE_ALLOWED_EXTENSIONS.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
