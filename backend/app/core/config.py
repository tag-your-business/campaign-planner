from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Campaign Planner"
    debug: bool = False

    # OpenAI
    openai_api_key: str = ""
    openai_text_model: str = "gpt-4o-mini"
    openai_image_model: str = "dall-e-3"

    # Data paths
    data_dir: str = "data"
    registry_path: str = "data/registry/company_registry.json"
    companies_dir: str = "data/companies"
    events_dir: str = "data/events"
    campaigns_dir: str = "data/campaigns"
    logs_dir: str = "data/logs"

    # Generation timing
    generation_lead_days: int = 10
    publish_lead_days: int = 3

    # Scheduler
    generate_cron: str = "0 8 * * *"  # daily 8 AM
    publish_cron: str = "0 10 * * *"  # daily 10 AM

    # Social media API versions
    facebook_api_version: str = "v21.0"
    instagram_api_version: str = "v21.0"
    facebook_access_token: str = ""
    instagram_access_token: str = ""

    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: int = 2


settings = Settings()
