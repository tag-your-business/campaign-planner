"""Core evaluation engine for running prompt evaluations."""

import json
from typing import Any, Callable

from deepeval.test_case import LLMTestCase

from .config_loader import EvaluationConfig, PromptVariation
from .metrics_factory import create_metric


class PromptEvaluator:
    """Evaluates multiple prompt variations against metrics."""

    def __init__(
        self,
        config: EvaluationConfig,
        generator_func: Callable[[dict, str, str, dict], tuple[Any, dict | None]],
    ):
        """Initialize evaluator.

        Args:
            config: Evaluation configuration
            generator_func: Function that generates output given:
                (campaign_spec, system_prompt, user_prompt, model_config)
                -> (output, usage_dict)
        """
        self.config = config
        self.generator_func = generator_func
        self.metrics = [create_metric(m) for m in config.metrics]

    def load_test_data(self) -> list[dict]:
        """Load test data from configured path."""
        with open(self.config.data_path) as f:
            return json.load(f)

    def load_prompt_variations(self) -> list[PromptVariation]:
        """Load prompt variations based on config.

        If prompts are specified in config, loads only those.
        Otherwise, loads all .yaml files from prompts directory.
        """
        prompts_dir = self.config.prompts_dir
        prompt_names = self.config.prompt_names
        variations = []

        if prompt_names:
            # Load only specified prompts
            for name in prompt_names:
                prompt_file = prompts_dir / f"{name}.yaml"
                if prompt_file.exists():
                    variations.append(PromptVariation(prompt_file))
                else:
                    raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        else:
            # Load all prompts from directory
            for prompt_file in sorted(prompts_dir.glob("*.yaml")):
                variations.append(PromptVariation(prompt_file))

        return variations

    def evaluate_prompt(
        self, variation: PromptVariation, test_data: list[dict], model_config: dict
    ) -> dict:
        """Evaluate a single prompt variation.

        Args:
            variation: Prompt variation to evaluate
            test_data: List of test campaign specs
            model_config: Model configuration to use for generation

        Returns:
            Dict with evaluation results including scores per metric
        """
        results = {
            "prompt_name": variation.name,
            "prompt_description": variation.description,
            "model_config": model_config,
            "test_cases": [],
            "total_usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }

        for spec in test_data:
            # Generate output using this prompt variation with model config
            actual_output, usage = self.generator_func(
                spec, variation.system_prompt, variation.user_prompt, model_config
            )

            # Accumulate token usage
            if usage:
                results["total_usage"]["prompt_tokens"] += usage.get("prompt_tokens", 0)
                results["total_usage"]["completion_tokens"] += usage.get(
                    "completion_tokens", 0
                )
                results["total_usage"]["total_tokens"] += usage.get("total_tokens", 0)

            # Create test case
            test_case = LLMTestCase(
                input=spec.get("input_description", ""),
                actual_output=actual_output,
                context=spec.get("context", []),
            )

            # Evaluate with all metrics
            test_result = {
                "campaign_spec": spec,
                "output": actual_output,
                "usage": usage,
                "metrics": {},
            }

            for metric in self.metrics:
                metric.measure(test_case)
                test_result["metrics"][metric.__name__] = {
                    "score": metric.score,
                    "success": metric.is_successful(),
                    "reason": metric.reason,
                }

            results["test_cases"].append(test_result)

        # Calculate aggregate scores
        results["aggregate_scores"] = self._calculate_aggregates(results)

        return results

    def _calculate_aggregates(self, results: dict) -> dict:
        """Calculate aggregate metric scores.

        Args:
            results: Results dict containing test_cases

        Returns:
            Dict mapping metric names to aggregate statistics
        """
        aggregates = {}
        test_cases = results["test_cases"]

        if not test_cases:
            return aggregates

        # Get all metric names
        metric_names = test_cases[0]["metrics"].keys()

        for metric_name in metric_names:
            scores = [tc["metrics"][metric_name]["score"] for tc in test_cases]
            success_count = sum(
                tc["metrics"][metric_name]["success"] for tc in test_cases
            )
            success_rate = success_count / len(test_cases)

            aggregates[metric_name] = {
                "mean_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
                "success_rate": success_rate,
            }

        return aggregates

    def save_results(self, results: dict, prompt_name: str):
        """Save results to results directory.

        Args:
            results: Evaluation results to save
            prompt_name: Name of the prompt variation
        """
        self.config.results_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.config.results_dir / f"{prompt_name}_results.json"

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
