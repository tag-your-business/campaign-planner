from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Campaign Planner"
    debug: bool = False

    # Text Generation Provider Selection
    text_generation_provider: str = "openai"  # openai, nvidia, or anthropic

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_text_model: str = "claude-opus-4-8"

    # OpenAI
    openai_api_key: str = ""
    openai_text_model: str = "gpt-4o-mini"
    openai_image_model: str = "dall-e-3"

    # NVIDIA
    nvidia_api_key: str = ""
    nvidia_text_model: str = "meta/llama-3.1-8b-instruct"

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

    # Testing — skip DALL-E and use data/assets/fallback_image.png instead
    use_fallback_image: bool = False

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
