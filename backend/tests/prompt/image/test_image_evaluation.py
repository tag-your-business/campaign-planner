"""Image generation evaluation tests."""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest
from app.features.generation.image import ImageService
from deepeval.test_case import LLMTestCase
from tests.prompt.framework.config_loader import EvaluationConfig
from tests.prompt.image.custom_metrics import (
    ImageGenerationSuccessMetric,
    TextPlacementMetric,
    VisualQualityScoreMetric,
)

pytestmark = [
    pytest.mark.eval,
    pytest.mark.skipif(
        os.environ.get("RUN_LLM_EVAL") != "1",
        reason="LLM eval tests skipped. Set RUN_LLM_EVAL=1 to run.",
    ),
]


class TestImageEvaluation:
    """Evaluate image generation with various prompts."""

    @pytest.fixture(scope="class")
    def feature_dir(self):
        """Get image feature directory."""
        return Path(__file__).parent

    @pytest.fixture(scope="class")
    def config(self, feature_dir):
        """Load image evaluation config."""
        return EvaluationConfig(feature_dir / "config.yaml")

    @pytest.fixture(scope="class")
    def test_data(self, feature_dir, config):
        """Load test data (campaign specs)."""
        with open(config.data_path) as f:
            return json.load(f)

    def load_prompt_files(self, config: EvaluationConfig) -> list[dict]:
        """Load all prompt files (both auto-generated and manual).

        Returns:
            List of prompt data dicts with 'name', 'source', and prompt content.
        """
        import yaml

        prompts_dir = config.prompts_dir
        prompt_files = []

        if not prompts_dir.exists():
            return prompt_files

        prompt_filter: list[str] = config.raw_config.get("prompt_filter") or []

        for prompt_file in sorted(prompts_dir.glob("*.yaml")):
            if prompt_filter and not any(
                prompt_file.stem.startswith(p) for p in prompt_filter
            ):
                continue

            with open(prompt_file) as f:
                data = yaml.safe_load(f)

            if prompt_file.name.startswith("prompt_auto_"):
                source = "auto"
            elif prompt_file.name.startswith("prompt_manual_"):
                source = "manual"
            else:
                source = "unknown"

            prompt_files.append(
                {
                    "name": prompt_file.stem,
                    "source": source,
                    "file_path": prompt_file,
                    "data": data,
                }
            )

        return prompt_files

    def test_evaluate_all_prompts(self, feature_dir, config, test_data):
        """Run evaluation for all image prompts with all configured models."""
        prompts = self.load_prompt_files(config)

        if not prompts:
            pytest.skip("No prompt files found in prompts/ directory")

        # Get image models from config
        image_models = config.image_models
        if not image_models:
            pytest.skip("No image models configured in config.yaml")

        images_dir = feature_dir / config.raw_config.get(
            "images_dir", "generated_images"
        )
        images_dir.mkdir(parents=True, exist_ok=True)

        results_dir = config.results_dir
        results_dir.mkdir(parents=True, exist_ok=True)

        # Initialize metrics
        success_metric = ImageGenerationSuccessMetric()
        quality_metric = VisualQualityScoreMetric()
        placement_metric = TextPlacementMetric()

        all_results = []

        for model_config in image_models:
            model_name = model_config.get("model", "unknown")
            print(f"\n{'='*60}")
            print(f"Image Model: {model_name}")
            print(
                f"Config: size={model_config.get('size')}, quality={model_config.get('quality')}"
            )

            # Create image service with model config
            image_service = ImageService(
                model=model_config.get("model"),
                size=model_config.get("size"),
                quality=model_config.get("quality"),
            )

            for prompt_info in prompts:
                print(
                    f"\n  Prompt: {prompt_info['name']} (source: {prompt_info['source']})"
                )

                prompt_data = prompt_info["data"]

                # Get the image prompt text
                image_prompt = prompt_data.get("image_prompt")
                if not image_prompt:
                    print("    Skipping - no image_prompt field found")
                    continue

                # Generate image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                model_slug = model_name.replace("-", "_")
                output_filename = f"{prompt_info['name']}_{model_slug}_{timestamp}.png"
                output_path = images_dir / output_filename

                try:
                    result_path = image_service.generate(image_prompt, output_path)
                    print(f"    Generated: {result_path}")

                    # Create test case for metrics
                    test_case = LLMTestCase(
                        input=image_prompt,
                        actual_output=str(result_path),
                    )

                    # Evaluate metrics
                    success_score = success_metric.measure(test_case)
                    quality_score = quality_metric.measure(test_case)
                    placement_score = placement_metric.measure(test_case)

                    result = {
                        "prompt_name": prompt_info["name"],
                        "source": prompt_info["source"],
                        "model": model_name,
                        "model_config": model_config,
                        "image_path": str(result_path),
                        "scores": {
                            "image_generation_success": success_score,
                            "visual_quality_score": quality_score,
                            "text_placement": placement_score,
                        },
                        "metrics_details": {
                            "success": {
                                "score": success_score,
                                "reason": success_metric.reason,
                            },
                            "quality": {
                                "score": quality_score,
                                "reason": quality_metric.reason,
                            },
                            "text_placement": {
                                "score": placement_score,
                                "reason": placement_metric.reason,
                            },
                        },
                        "source_info": prompt_data.get("source_info", {}),
                    }

                    all_results.append(result)

                    print(f"    Success: {success_score:.2f} - {success_metric.reason}")
                    print(f"    Quality: {quality_score:.2f} - {quality_metric.reason}")
                    print(
                        f"    Placement: {placement_score:.2f} - {placement_metric.reason}"
                    )

                except Exception as e:
                    print(f"    Error generating image: {e}")
                    all_results.append(
                        {
                            "prompt_name": prompt_info["name"],
                            "source": prompt_info["source"],
                            "model": model_name,
                            "error": str(e),
                            "scores": {
                                "image_generation_success": 0.0,
                                "visual_quality_score": 0.0,
                                "text_placement": 0.0,
                            },
                        }
                    )

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"evaluation_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump(
                {
                    "timestamp": timestamp,
                    "models_tested": [m.get("model") for m in image_models],
                    "prompts_evaluated": len(all_results),
                    "results": all_results,
                },
                f,
                indent=2,
            )

        print(f"\n{'='*60}")
        print(f"Results saved to: {results_file}")
        print(f"Prompts evaluated: {len(all_results)}")

        # Calculate aggregate scores
        if all_results:
            success_avg = sum(
                r["scores"]["image_generation_success"] for r in all_results
            ) / len(all_results)
            quality_avg = sum(
                r["scores"]["visual_quality_score"] for r in all_results
            ) / len(all_results)
            placement_avg = sum(
                r["scores"]["text_placement"] for r in all_results
            ) / len(all_results)
            print(f"Average success score: {success_avg:.2f}")
            print(f"Average quality score: {quality_avg:.2f}")
            print(f"Average text placement score: {placement_avg:.2f}")

        assert len(all_results) > 0, "No prompts were evaluated"
