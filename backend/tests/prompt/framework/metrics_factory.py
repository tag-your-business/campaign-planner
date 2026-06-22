"""Create DeepEval metrics from configuration."""

from deepeval.metrics import AnswerRelevancyMetric, BaseMetric, GEval
from deepeval.test_case import LLMTestCaseParams


def create_metric(metric_config: dict) -> BaseMetric:
    """Create a metric from configuration.

    Args:
        metric_config: Dict with keys:
            - type: "answer_relevancy", "geval", "custom"
            - name: Metric name
            - threshold: Score threshold
            - For GEval:
                - criteria: Evaluation criteria
                - evaluation_steps: List of steps

    Returns:
        Instantiated metric ready for evaluation

    Raises:
        ValueError: If metric type is unknown
    """
    metric_type = metric_config["type"]
    threshold = metric_config.get("threshold", 0.7)

    if metric_type == "answer_relevancy":
        return AnswerRelevancyMetric(threshold=threshold)

    elif metric_type == "geval":
        return GEval(
            name=metric_config["name"],
            criteria=metric_config["criteria"],
            evaluation_steps=metric_config["evaluation_steps"],
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
            threshold=threshold,
        )

    elif metric_type == "custom":
        # Import and instantiate custom metric
        module_path, class_name = metric_config["class"].rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        metric_class = getattr(module, class_name)
        return metric_class(**metric_config.get("params", {}))

    else:
        raise ValueError(f"Unknown metric type: {metric_type}")
