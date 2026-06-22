"""Image prompt generation evaluation tests."""

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from app.common.ai_providers import Message, ProviderFactory, TextGenerationRequest
from tests.prompt.framework.comparison import ComparisonGenerator
from tests.prompt.framework.config_loader import EvaluationConfig
from tests.prompt.framework.evaluator import PromptEvaluator

pytestmark = [
    pytest.mark.eval,
    pytest.mark.skipif(
        os.environ.get("RUN_LLM_EVAL") != "1",
        reason="LLM eval tests skipped. Set RUN_LLM_EVAL=1 to run.",
    ),
]


class TestImagePromptEvaluation:
    """Evaluate image prompt generation with multiple prompt variations."""

    @pytest.fixture(scope="class")
    def feature_dir(self):
        """Get image_prompt feature directory."""
        return Path(__file__).parent

    @pytest.fixture(scope="class")
    def config(self, feature_dir):
        """Load image prompt evaluation config."""
        return EvaluationConfig(feature_dir / "config.yaml")

    @pytest.fixture(scope="class")
    def provider(self):
        """Get AI provider for generation."""
        return ProviderFactory.create()

    def generator_func(
        self, spec: dict, system_prompt: str, user_prompt: str, model_config: dict
    ) -> tuple[str, dict | None]:
        """Generate image prompt with custom prompts and model configuration.

        Args:
            spec: Campaign specification
            system_prompt: Custom system prompt
            user_prompt: Custom user prompt template
            model_config: Model configuration dict with provider, model, etc.

        Returns:
            Tuple of (generated image prompt string, usage dict with token counts)
        """
        # Handle brand_colors formatting
        brand_colors = spec.get("brand_colors", {})
        if isinstance(brand_colors, dict):
            primary = brand_colors.get("primary", "")
            accent = brand_colors.get("accent", "")
            colors_text = ", ".join(filter(None, [primary, accent]))
        else:
            colors_text = ", ".join(brand_colors) if brand_colors else ""

        # Handle location text
        locations = spec.get("locations", [])
        primary_loc = next((loc for loc in locations if loc.get("is_primary")), None)
        location_text = ""
        if primary_loc:
            parts = [
                p
                for p in [
                    primary_loc.get("city", ""),
                    primary_loc.get("state", ""),
                    primary_loc.get("country", ""),
                ]
                if p
            ]
            location_text = ", ".join(parts)

        # Handle tone_keywords
        tone_keywords = spec.get("tone_keywords", [])
        tone_text = ", ".join(tone_keywords) if tone_keywords else "professional"

        # Format user prompt with spec values
        formatted_user_prompt = user_prompt.format(
            event_name=spec.get("event_name", ""),
            industry=spec.get("industry", ""),
            tone_keywords=tone_text,
            brand_colors=colors_text if colors_text else "natural vibrant tones",
            visual_style=spec.get("visual_style", "photorealistic"),
            primary_audience=spec.get("primary_audience", ""),
            location_text=location_text if location_text else "general",
            language=spec.get("language", "English"),
        )

        # Get model configuration with defaults
        provider_name = model_config.get("provider")
        model = model_config.get("model")
        temperature = model_config.get("temperature", 0.7)
        max_tokens = model_config.get("max_tokens", 800)
        extra_params = model_config.get("extra_params")

        # Create provider and generate
        provider = ProviderFactory.create(provider_name)
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content=system_prompt),
                Message(role="user", content=formatted_user_prompt),
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_params=extra_params,
        )

        response = provider.generate(request)
        return response.text, response.usage

    def _generate_auto_prompt_file(
        self,
        variation_name: str,
        model_config: dict,
        image_prompt: str,
        spec: dict,
        scores: dict,
        output_dir: Path,
        file_prefix: str,
    ):
        """Generate auto prompt file for image evaluation cascade.

        Args:
            variation_name: Name of the prompt variation (e.g., "prompt_v1")
            model_config: Model configuration used for generation
            image_prompt: The generated image prompt text
            spec: Campaign specification used
            scores: Evaluation scores for this generation
            output_dir: Directory to write the auto prompt file
            file_prefix: Prefix for the output file (e.g., "prompt_auto_")
        """
        model_name = model_config.get("model", "unknown")
        # Clean model name for filename
        model_short = model_name.replace("/", "-").replace(".", "-")

        # Extract just the version part from variation name
        source_name = variation_name.replace("prompt_", "")

        filename = f"{file_prefix}{source_name}_{model_short}.yaml"
        output_path = output_dir / filename

        output_dir.mkdir(parents=True, exist_ok=True)

        auto_prompt_data = {
            "description": (
                f"Auto-generated from image_prompt eval ({variation_name} with {model_name})"
            ),
            "source_info": {
                "prompt_name": variation_name,
                "model_provider": model_config.get("provider", "openai"),
                "model_name": model_name,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "evaluation_scores": scores,
            },
            "image_prompt": image_prompt,
            "campaign_spec": {
                "event_name": spec.get("event_name"),
                "industry": spec.get("industry"),
            },
        }

        with open(output_path, "w") as f:
            yaml.dump(auto_prompt_data, f, default_flow_style=False, allow_unicode=True)

        print(f"  Generated auto prompt file: {output_path}")

    def test_evaluate_all_prompts(self, config, feature_dir):
        """Run evaluation for all prompt variations across all configured models."""
        evaluator = PromptEvaluator(config=config, generator_func=self.generator_func)

        # Load test data
        test_data = evaluator.load_test_data()

        # Load all prompt variations
        variations = evaluator.load_prompt_variations()

        assert len(variations) > 0, "No prompt variations found"

        # Get all models to test (from config.yaml)
        config_models = config.models

        # Check if image eval cascade is enabled
        run_image_eval = config.raw_config.get("run_image_eval", False)
        image_eval_config = config.raw_config.get("image_eval_config", {})

        total_evaluations = 0

        # Evaluate each variation with each model
        for variation in variations:
            print(f"\n{'='*60}")
            print(f"Prompt Variation: {variation.name}")
            print(f"Description: {variation.description}")
            print(f"Testing with {len(config_models)} model(s)")

            for model_config in config_models:
                provider = model_config.get("provider") or "default"
                model = model_config.get("model") or "default"
                print(f"\n  Testing with: {provider}/{model}")

                results = evaluator.evaluate_prompt(variation, test_data, model_config)

                # Save with both prompt and model name
                model_short = model.split("/")[-1] if "/" in model else model
                result_name = f"{variation.name}_{model_short}"
                evaluator.save_results(results, result_name)

                print(f"  Results saved: {result_name}")
                print(f"  Aggregate scores: {results['aggregate_scores']}")

                # Generate auto prompt files if cascade is enabled
                if run_image_eval:
                    output_dir = feature_dir / image_eval_config.get(
                        "output_dir", "../image/prompts"
                    )
                    file_prefix = image_eval_config.get("file_prefix", "prompt_auto_")

                    # Generate auto prompt for each test case
                    for i, test_case in enumerate(results.get("test_cases", [])):
                        spec = test_data[i] if i < len(test_data) else {}
                        self._generate_auto_prompt_file(
                            variation_name=variation.name,
                            model_config=model_config,
                            image_prompt=test_case.get("output", ""),
                            spec=spec,
                            scores=test_case.get("metrics", {}),
                            output_dir=output_dir,
                            file_prefix=file_prefix,
                        )

                total_evaluations += 1

        # Generate comparison summary
        print(f"\n{'='*60}")
        print(f"Generating comparison across {total_evaluations} evaluations...")

        comparison_gen = ComparisonGenerator(config.results_dir)
        comparison = comparison_gen.generate_comparison()
        comparison_gen.save_comparison(comparison)

        print(f"\nOverall winner: {comparison['overall_winner']}")
        print(f"Comparison report saved to {config.results_dir}/comparison_report.md")

        # Assert that comparison was generated successfully
        assert "overall_winner" in comparison
        assert comparison["prompts_compared"] == total_evaluations
