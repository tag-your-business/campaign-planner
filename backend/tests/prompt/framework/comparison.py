"""Generate comparison summaries across prompt variations."""

import json
from pathlib import Path

from .config_loader import get_providers_registry


class ComparisonGenerator:
    """Generates comparison summaries for multiple prompt evaluations."""

    def __init__(self, results_dir: Path):
        self.results_dir = results_dir
        self.providers_registry = get_providers_registry()

    def load_all_results(self) -> list[dict]:
        """Load all result files from results directory.

        Returns:
            List of result dictionaries from all prompt evaluations
        """
        results = []
        for result_file in self.results_dir.glob("*_results.json"):
            if result_file.name == "comparison_summary.json":
                continue
            with open(result_file) as f:
                results.append(json.load(f))
        return results

    def calculate_cost(self, usage: dict, pricing: dict | None) -> float:
        """Calculate cost from token usage and pricing.

        Args:
            usage: Dict with prompt_tokens and completion_tokens
            pricing: Dict with prompt and completion prices per 1M tokens

        Returns:
            Total cost in USD
        """
        if not usage or not pricing:
            return 0.0

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        prompt_price = pricing.get("prompt", 0.0)
        completion_price = pricing.get("completion", 0.0)

        # Prices are per 1M tokens
        cost = (prompt_tokens * prompt_price / 1_000_000) + (
            completion_tokens * completion_price / 1_000_000
        )

        return cost

    def get_model_pricing(self, model_config: dict) -> dict | None:
        """Get pricing for a model from the providers registry.

        Args:
            model_config: Model configuration dict

        Returns:
            Pricing dict or None if not found
        """
        provider = model_config.get("provider")
        model = model_config.get("model")

        # Try to find pricing in registry
        for config_name, config in self.providers_registry.items():
            if (
                config.get("provider") == provider
                and config.get("model") == model
                and "pricing" in config
            ):
                return config["pricing"]

        return None

    def generate_comparison(self) -> dict:
        """Generate comparison summary across all prompts.

        Returns:
            Dict with comparison data and winner determination
        """
        all_results = self.load_all_results()

        if not all_results:
            return {"error": "No results found"}

        comparison = {
            "prompts_compared": len(all_results),
            "metrics_comparison": {},
            "token_cost_comparison": [],
            "overall_ranking": [],
        }

        # Get all metric names
        metric_names = list(all_results[0]["aggregate_scores"].keys())

        # Compare each metric across prompts
        for metric_name in metric_names:
            metric_comparison = []

            for result in all_results:
                agg = result["aggregate_scores"][metric_name]
                model_cfg = result.get("model_config", {})
                provider = model_cfg.get("provider") or "default"
                model = model_cfg.get("model") or "default"

                metric_comparison.append(
                    {
                        "prompt_name": result["prompt_name"],
                        "prompt_description": result["prompt_description"],
                        "model": f"{provider}/{model}",
                        "mean_score": agg["mean_score"],
                        "success_rate": agg["success_rate"],
                    }
                )

            # Sort by mean score
            metric_comparison.sort(key=lambda x: x["mean_score"], reverse=True)

            comparison["metrics_comparison"][metric_name] = {
                "rankings": metric_comparison,
                "winner": metric_comparison[0]["prompt_name"],
                "winner_score": metric_comparison[0]["mean_score"],
            }

        # Calculate token usage and cost for each prompt/model
        for result in all_results:
            model_cfg = result.get("model_config", {})
            provider = model_cfg.get("provider") or "default"
            model = model_cfg.get("model") or "default"
            usage = result.get("total_usage", {})
            pricing = self.get_model_pricing(model_cfg)
            cost = self.calculate_cost(usage, pricing)

            comparison["token_cost_comparison"].append(
                {
                    "prompt_name": result["prompt_name"],
                    "model": f"{provider}/{model}",
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "cost_usd": cost,
                }
            )

        # Sort by cost
        comparison["token_cost_comparison"].sort(key=lambda x: x["cost_usd"])

        # Calculate overall ranking (average rank across metrics)
        prompt_ranks = {}
        for metric_name, data in comparison["metrics_comparison"].items():
            for idx, item in enumerate(data["rankings"]):
                prompt_name = item["prompt_name"]
                if prompt_name not in prompt_ranks:
                    prompt_ranks[prompt_name] = []
                prompt_ranks[prompt_name].append(idx + 1)  # Rank starts at 1

        # Calculate average rank
        overall_ranking = []
        for prompt_name, ranks in prompt_ranks.items():
            avg_rank = sum(ranks) / len(ranks)
            overall_ranking.append(
                {
                    "prompt_name": prompt_name,
                    "average_rank": avg_rank,
                    "rank_details": dict(zip(metric_names, ranks)),
                }
            )

        overall_ranking.sort(key=lambda x: x["average_rank"])
        comparison["overall_ranking"] = overall_ranking
        comparison["overall_winner"] = overall_ranking[0]["prompt_name"]

        return comparison

    def save_comparison(self, comparison: dict):
        """Save comparison summary and generate markdown report.

        Args:
            comparison: Comparison data to save
        """
        output_file = self.results_dir / "comparison_summary.json"
        with open(output_file, "w") as f:
            json.dump(comparison, f, indent=2)

        # Also generate markdown report
        self._generate_markdown_report(comparison)

    def _generate_markdown_report(self, comparison: dict):
        """Generate human-readable markdown report.

        Args:
            comparison: Comparison data to format as markdown
        """
        lines = ["# Prompt Evaluation Comparison\n"]
        lines.append(f"**Prompts Compared:** {comparison['prompts_compared']}\n")
        lines.append(f"**Overall Winner:** {comparison['overall_winner']}\n")

        lines.append("\n## Overall Ranking\n")
        lines.append("| Rank | Prompt | Model | Average Rank | Rank Details |")
        lines.append("|------|--------|-------|--------------|--------------|")

        for idx, item in enumerate(comparison["overall_ranking"], 1):
            rank_details = ", ".join(
                f"{k}: #{v}" for k, v in item["rank_details"].items()
            )
            # Get model info from first metric comparison
            first_metric = list(comparison["metrics_comparison"].values())[0]
            model_info = next(
                (
                    r["model"]
                    for r in first_metric["rankings"]
                    if r["prompt_name"] == item["prompt_name"]
                ),
                "unknown",
            )
            lines.append(
                f"| {idx} | {item['prompt_name']} | {model_info} | "
                f"{item['average_rank']:.2f} | {rank_details} |"
            )

        lines.append("\n## Token Usage and Cost Comparison\n")
        lines.append(
            "| Prompt | Model | Prompt Tokens | Completion Tokens | "
            "Total Tokens | Cost (USD) |"
        )
        lines.append(
            "|--------|-------|---------------|-------------------|--------------|------------|"
        )

        for item in comparison["token_cost_comparison"]:
            lines.append(
                f"| {item['prompt_name']} | {item['model']} | "
                f"{item['prompt_tokens']:,} | {item['completion_tokens']:,} | "
                f"{item['total_tokens']:,} | ${item['cost_usd']:.6f} |"
            )

        # Add cost summary
        total_cost = sum(
            item["cost_usd"] for item in comparison["token_cost_comparison"]
        )
        lines.append(f"\n**Total Cost:** ${total_cost:.6f}\n")

        if comparison["token_cost_comparison"]:
            cheapest = comparison["token_cost_comparison"][0]
            most_expensive = comparison["token_cost_comparison"][-1]
            lines.append(
                f"**Most Cost-Efficient:** {cheapest['prompt_name']} "
                f"with {cheapest['model']} (${cheapest['cost_usd']:.6f})\n"
            )
            lines.append(
                f"**Most Expensive:** {most_expensive['prompt_name']} "
                f"with {most_expensive['model']} (${most_expensive['cost_usd']:.6f})\n"
            )

        lines.append("\n## Metric-by-Metric Comparison\n")

        for metric_name, data in comparison["metrics_comparison"].items():
            lines.append(f"\n### {metric_name}\n")
            lines.append(
                f"**Winner:** {data['winner']} (score: {data['winner_score']:.3f})\n"
            )

            lines.append("| Rank | Prompt | Model | Mean Score | Success Rate |")
            lines.append("|------|--------|-------|------------|--------------|")

            for idx, item in enumerate(data["rankings"], 1):
                lines.append(
                    f"| {idx} | {item['prompt_name']} | {item['model']} | "
                    f"{item['mean_score']:.3f} | "
                    f"{item['success_rate']:.1%} |"
                )

        report_file = self.results_dir / "comparison_report.md"
        with open(report_file, "w") as f:
            f.write("\n".join(lines))
