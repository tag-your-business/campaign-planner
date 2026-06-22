"""Caption generation evaluation tests."""

from pathlib import Path

import pytest
from app.common.ai_providers import Message, ProviderFactory, TextGenerationRequest
from tests.prompt.framework.comparison import ComparisonGenerator
from tests.prompt.framework.config_loader import EvaluationConfig
from tests.prompt.framework.evaluator import PromptEvaluator

pytestmark = pytest.mark.eval


class TestCaptionEvaluation:
    """Evaluate caption generation with multiple prompt variations."""

    @pytest.fixture(scope="class")
    def feature_dir(self):
        """Get caption feature directory."""
        return Path(__file__).parent

    @pytest.fixture(scope="class")
    def config(self, feature_dir):
        """Load caption evaluation config."""
        return EvaluationConfig(feature_dir / "config.yaml")

    @pytest.fixture(scope="class")
    def provider(self):
        """Get AI provider for generation."""
        return ProviderFactory.create()

    def generator_func(
        self, spec: dict, system_prompt: str, user_prompt: str, model_config: dict
    ) -> tuple[str, dict | None]:
        """Generate caption with custom prompts and model configuration.

        Args:
            spec: Campaign specification
            system_prompt: Custom system prompt
            user_prompt: Custom user prompt template
            model_config: Model configuration dict with provider, model, etc.

        Returns:
            Tuple of (generated caption string, usage dict with token counts)
        """
        # Format user prompt with spec values
        formatted_user_prompt = user_prompt.format(
            event_name=spec.get("event_name", ""),
            company_name=spec.get("company_name", ""),
            industry=spec.get("industry", ""),
            tone=spec.get("tone", ""),
            event_tags=", ".join(spec.get("event_tags", [])),
        )

        # Get model configuration with defaults
        provider_name = model_config.get("provider")
        model = model_config.get("model")
        temperature = model_config.get("temperature", 0.7)
        max_tokens = model_config.get("max_tokens", 200)

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
        )

        response = provider.generate(request)
        return response.text, response.usage

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
                total_evaluations += 1

        # Generate comparison summary
        print(f"\n{'='*60}")
        print(f"Generating comparison across {total_evaluations} evaluations...")

        comparison_gen = ComparisonGenerator(config.results_dir)
        comparison = comparison_gen.generate_comparison()
        comparison_gen.save_comparison(comparison)

        print(f"\nOverall winner: {comparison['overall_winner']}")
        print(
            f"Comparison report saved to " f"{config.results_dir}/comparison_report.md"
        )

        # Assert that comparison was generated successfully
        assert "overall_winner" in comparison
        assert comparison["prompts_compared"] == total_evaluations
