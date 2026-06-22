"""Load and parse configuration files for evaluation."""

from pathlib import Path

import yaml

# Load global registries once
_FRAMEWORK_DIR = Path(__file__).parent
_PROVIDERS_REGISTRY = None
_METRICS_REGISTRY = None


def _load_registry(registry_file: str) -> dict:
    """Load a registry YAML file."""
    registry_path = _FRAMEWORK_DIR / registry_file
    if registry_path.exists():
        with open(registry_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def get_providers_registry() -> dict:
    """Get the providers registry, loading it if needed."""
    global _PROVIDERS_REGISTRY
    if _PROVIDERS_REGISTRY is None:
        _PROVIDERS_REGISTRY = _load_registry("providers.yaml")
    return _PROVIDERS_REGISTRY


def get_metrics_registry() -> dict:
    """Get the metrics registry, loading it if needed."""
    global _METRICS_REGISTRY
    if _METRICS_REGISTRY is None:
        _METRICS_REGISTRY = _load_registry("metrics.yaml")
    return _METRICS_REGISTRY


class EvaluationConfig:
    """Configuration for a feature evaluation."""

    def __init__(self, config_path: Path):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.config_dir = config_path.parent

    @property
    def system_prompt(self) -> str:
        """Get system prompt from config."""
        return self.config.get("system_prompt", "")

    @property
    def user_prompt_template(self) -> str:
        """Get user prompt template."""
        return self.config.get("user_prompt", "")

    @property
    def prompts_dir(self) -> Path:
        """Get prompts directory path."""
        prompts_path = self.config.get("prompts_dir", "prompts")
        if not Path(prompts_path).is_absolute():
            return self.config_dir / prompts_path
        return Path(prompts_path)

    @property
    def metrics(self) -> list[dict]:
        """Get metrics configuration, resolving references from registry.

        Supports:
        - String references: "answer_relevancy" -> looks up in metrics.yaml
        - Dict with full definition: {"type": "geval", ...}
        - Dict with overrides: {"ref": "coherence", "threshold": 0.9}
        """
        metrics_config = self.config.get("metrics", [])
        metrics_registry = get_metrics_registry()
        resolved_metrics = []

        for metric in metrics_config:
            if isinstance(metric, str):
                # Simple string reference - lookup in registry
                if metric in metrics_registry:
                    resolved_metrics.append(metrics_registry[metric])
                else:
                    raise ValueError(f"Metric '{metric}' not found in metrics registry")
            elif isinstance(metric, dict):
                if "ref" in metric:
                    # Reference with overrides
                    ref_name = metric["ref"]
                    if ref_name not in metrics_registry:
                        raise ValueError(
                            f"Metric '{ref_name}' not found in metrics registry"
                        )
                    # Start with registry definition, then apply overrides
                    base_metric = metrics_registry[ref_name].copy()
                    overrides = {k: v for k, v in metric.items() if k != "ref"}
                    base_metric.update(overrides)
                    resolved_metrics.append(base_metric)
                else:
                    # Full inline definition
                    resolved_metrics.append(metric)
            else:
                raise ValueError(f"Invalid metric configuration: {metric}")

        return resolved_metrics

    @property
    def data_path(self) -> Path:
        """Get test data path."""
        data_path = self.config.get("data_path", "data/campaign_specs.json")
        if not Path(data_path).is_absolute():
            return self.config_dir / data_path
        return Path(data_path)

    @property
    def results_dir(self) -> Path:
        """Get results directory."""
        results_path = self.config.get("results_dir", "results")
        if not Path(results_path).is_absolute():
            return self.config_dir / results_path
        return Path(results_path)

    @property
    def models(self) -> list[dict]:
        """Get model configurations from config, resolving from registry.

        Returns list of model configs. Supports:
        - Single model: model: "gpt4o_mini"
        - Multiple models: model: ["gpt4o_mini", "claude_sonnet"]
        - Inline dict: model: {provider: "openai", model: "gpt-4o"}

        Raises:
            ValueError: If model is not specified in config
        """
        if "model" not in self.config:
            raise ValueError(
                "model must be specified in config.yaml. "
                "Reference a provider from framework/providers.yaml "
                "(e.g., model: 'gpt4o_mini')"
            )

        model_config = self.config["model"]
        providers_registry = get_providers_registry()

        # Handle list of models
        if isinstance(model_config, list):
            resolved_models = []
            for m in model_config:
                if isinstance(m, str):
                    if m not in providers_registry:
                        raise ValueError(
                            f"Provider '{m}' not found in providers registry. "
                            f"Available: {', '.join(providers_registry.keys())}"
                        )
                    resolved_models.append(providers_registry[m])
                elif isinstance(m, dict):
                    resolved_models.append(m)
                else:
                    raise ValueError(f"Invalid model config: {m}")
            return resolved_models

        # Handle single model (string or dict)
        if isinstance(model_config, str):
            if model_config not in providers_registry:
                raise ValueError(
                    f"Provider '{model_config}' not found in providers registry. "
                    f"Available: {', '.join(providers_registry.keys())}"
                )
            return [providers_registry[model_config]]

        if isinstance(model_config, dict):
            return [model_config]

        raise ValueError(f"Invalid model configuration: {model_config}")

    @property
    def default_model(self) -> dict:
        """Get first model configuration (for backward compatibility).

        Returns the first model from the models list.
        """
        return self.models[0]

    def get_model_config(self, model_name: str | None = None) -> dict:
        """Get model configuration by name, resolving from registry.

        Args:
            model_name: Model config name to lookup in providers.yaml

        Returns:
            Model configuration dict with provider, model, temperature, max_tokens

        Supports:
        - String reference: "gpt4o" -> looks up in providers.yaml
        - Dict with full definition: {"provider": "openai", ...}
        - None: Returns default_model
        """
        if not model_name:
            return self.default_model

        providers_registry = get_providers_registry()

        # Check if it's a reference to the registry
        if isinstance(model_name, str) and model_name in providers_registry:
            return providers_registry[model_name]

        # If it's a dict, return as-is (inline definition)
        if isinstance(model_name, dict):
            return model_name

        # Not found
        raise ValueError(f"Provider '{model_name}' not found in providers registry")


class PromptVariation:
    """A single prompt variation to test."""

    def __init__(self, prompt_file: Path):
        with open(prompt_file) as f:
            self.data = yaml.safe_load(f)
        self.name = prompt_file.stem

    @property
    def system_prompt(self) -> str:
        return self.data.get("system_prompt", "")

    @property
    def user_prompt(self) -> str:
        return self.data.get("user_prompt", "")

    @property
    def description(self) -> str:
        return self.data.get("description", "")
