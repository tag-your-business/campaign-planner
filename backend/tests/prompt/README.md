# DeepEval Prompt Evaluation Framework

Config-driven framework for evaluating and comparing prompt variations using DeepEval.

## Structure

```
backend/tests/prompt/
├── framework/                     # Shared framework code
│   ├── config_loader.py          # Load and parse config.yaml files
│   ├── evaluator.py              # Core evaluation engine
│   ├── metrics_factory.py        # Create metrics from config
│   ├── comparison.py             # Generate comparison summaries
│   ├── providers.yaml            # 🆕 Provider/Model registry (global)
│   └── metrics.yaml              # 🆕 Metrics registry (global)
│
├── caption/                       # Caption generation evaluation
│   ├── config.yaml               # Caption-specific configuration
│   ├── data/
│   │   └── campaign_specs.json  # Test campaign specifications
│   ├── prompts/
│   │   ├── prompt_v1.yaml       # Original prompt
│   │   ├── prompt_v2.yaml       # Emoji/CTA variation
│   │   └── prompt_v3.yaml       # Storytelling variation
│   ├── custom_metrics.py        # Caption-specific metrics
│   └── test_caption_evaluation.py  # Test runner
│
└── conftest.py                   # Shared pytest fixtures
```

## Dependency Conflict (IMPORTANT)

There is a **dependency conflict** with DeepEval that needs to be resolved:

**Issue:** DeepEval requires `openai <2.0.0`, but this project uses `openai >=2.41.0`.

### Solutions

#### Option 1: Wait for DeepEval Update (Recommended)
Monitor DeepEval for updates that support openai 2.x:
- Check: https://github.com/confident-ai/deepeval
- The framework is ready to use once DeepEval updates their dependencies

#### Option 2: Use OpenAI 1.x Temporarily
If you need to run evaluations immediately:

1. Create a separate virtual environment for prompt evaluation:
```bash
python -m venv prompt-eval-env
source prompt-eval-env/bin/activate
pip install "openai<2.0.0" "deepeval>=1.0.0" pyyaml pytest
```

2. Run evaluations in that environment:
```bash
cd backend/tests/prompt/caption
pytest test_caption_evaluation.py -v -s
```

3. Switch back to main environment for application development

#### Option 3: Alternative Evaluation Framework
Adapt the framework to use an alternative evaluation library:
- Replace DeepEval metrics with custom implementations
- Use direct OpenAI API calls for evaluation
- Framework structure (config-driven, comparison engine) remains the same

## Registry Pattern

The framework uses **global registries** to keep config files clean and DRY (Don't Repeat Yourself).

### Provider Registry (`framework/providers.yaml`)

Define all models once, reference them everywhere:

```yaml
# In framework/providers.yaml
gpt4o:
  provider: "openai"
  model: "gpt-4o"
  temperature: 0.7
  max_tokens: 200

claude_sonnet:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 200
```

Then reference by name:

```yaml
# In config.yaml
default_model: "gpt4o_mini"

# In prompt_v2.yaml
model: "claude_sonnet"
```

**Available providers:**
- `default` - Uses environment settings
- `gpt4o`, `gpt4o_mini`, `gpt4_turbo` - OpenAI models
- `claude_opus`, `claude_sonnet`, `claude_haiku` - Anthropic models
- `nvidia_llama` - NVIDIA models
- `gpt4o_creative`, `claude_creative` - High temperature variants
- `gpt4o_precise`, `claude_precise` - Low temperature variants
- And more... (see `framework/providers.yaml`)

### Metrics Registry (`framework/metrics.yaml`)

Define all metrics once, reference them everywhere:

```yaml
# In framework/metrics.yaml
coherence:
  type: "geval"
  name: "Coherence"
  criteria: "The text should be clear, fluent, and coherent"
  threshold: 0.7
  evaluation_steps:
    - "Check for clarity..."
```

Then reference by name:

```yaml
# In config.yaml
metrics:
  - "coherence"           # Simple reference
  - "answer_relevancy"    # Another reference
  - ref: "tone_matching"  # Reference with override
    threshold: 0.85
```

**Available metrics:**
- **DeepEval Built-in:** `answer_relevancy`, `answer_relevancy_strict`
- **Text Quality:** `coherence`, `coherence_strict`, `creativity`, `professionalism`
- **Engagement:** `engagement`, `tone_matching`, `brand_alignment`
- **Caption-Specific:** `caption_length`, `hashtag_count` (+ variants)
- **General:** `completeness`, `accuracy`, `conciseness`
- And more... (see `framework/metrics.yaml`)

### Benefits

1. **Single Source of Truth** - Define models and metrics once
2. **Clean Config Files** - No repetitive definitions
3. **Easy Maintenance** - Update in one place, affects all configs
4. **Reusability** - Share configs across caption, image_prompt, image features
5. **Consistency** - Ensure same settings across evaluations

## Usage (Once Dependencies Resolved)

### Running Caption Evaluation

```bash
cd backend
poetry run pytest tests/prompt/caption/test_caption_evaluation.py -v -s -m eval
```

### Adding New Prompt Variations

1. Create new prompt file: `tests/prompt/caption/prompts/prompt_v4.yaml`
```yaml
description: "Your variation description"
system_prompt: |
  Your system prompt here

user_prompt: |
  Your user prompt template with {placeholders}
```

2. Run evaluation (automatically includes all prompt variations):
```bash
poetry run pytest tests/prompt/caption/test_caption_evaluation.py -v -s
```

3. View comparison:
```bash
cat tests/prompt/caption/results/comparison_report.md
```

### Testing Same Prompt on Multiple Models

To compare how the same prompt performs on different models:

1. Create multiple prompt files with same content but different models:

```bash
# prompt_gpt4o.yaml
description: "Standard prompt on GPT-4o"
model: "gpt4o"
system_prompt: |
  Your prompt here

# prompt_claude.yaml
description: "Standard prompt on Claude Sonnet"
model: "claude_sonnet"
system_prompt: |
  Your prompt here  # Same as above
```

2. Run evaluation - the framework will test both and compare results

3. The comparison report will show model information:
```
| Rank | Prompt | Model | Mean Score |
|------|--------|-------|------------|
| 1 | prompt_gpt4o | openai/gpt-4o | 0.85 |
| 2 | prompt_claude | anthropic/claude-sonnet-4 | 0.82 |
```

### Configuring Models

Models are defined in `framework/providers.yaml` and referenced by name.

#### In config.yaml (REQUIRED)

```yaml
# Single model
model: "gpt4o_mini"

# Multiple models (tests all prompts with each model)
model:
  - "gpt4o_mini"
  - "claude_sonnet"
  - "gpt4o"

# All configs must explicitly set model - no hidden defaults!
```

When you specify multiple models, the framework will:
1. Test **each prompt variation** with **each model**
2. Generate separate result files: `prompt_v1_gpt4o_mini.json`, `prompt_v1_claude_sonnet.json`, etc.
3. Compare ALL combinations in the final report

Example: 3 prompts × 3 models = 9 total evaluations

#### In Prompt Variations

```yaml
description: "My prompt variation"

# Option 1: Reference from registry
model: "claude_sonnet"

# Option 2: Inline configuration (overrides registry)
model:
  provider: "openai"
  model: "gpt-4o-mini"
  temperature: 0.9
  max_tokens: 300

system_prompt: |
  Your system prompt here
```

#### Adding New Models to Registry

Edit `framework/providers.yaml`:

```yaml
my_custom_model:
  provider: "openai"
  model: "gpt-4o-mini"
  temperature: 0.8
  max_tokens: 250
```

Then reference anywhere: `model: "my_custom_model"`

**Priority Order:**
1. Inline `model` dict in prompt variation (highest)
2. Named `model` reference in prompt variation (from providers.yaml)
3. `model` from config.yaml (lowest)

### Adding New Metrics

Metrics are defined in `framework/metrics.yaml` and referenced by name.

#### Using Existing Metrics

In `config.yaml`:

```yaml
metrics:
  - "answer_relevancy"    # Simple reference
  - "coherence"          # Another reference
  - "caption_length"     # Custom metric
```

#### With Parameter Overrides

```yaml
metrics:
  - ref: "coherence"
    threshold: 0.85      # Override default threshold

  - ref: "caption_length"
    params:
      min_length: 100    # Override default params
      max_length: 250
```

#### Adding New Metrics to Registry

Edit `framework/metrics.yaml`:

```yaml
my_custom_metric:
  type: "geval"
  name: "My Custom Metric"
  criteria: "Evaluation criteria"
  threshold: 0.7
  evaluation_steps:
    - "Step 1"
    - "Step 2"
```

Then reference: `metrics: ["my_custom_metric"]`

#### Inline Metric Definition

For one-off metrics, use inline definition in `config.yaml`:

```yaml
metrics:
  - type: "geval"
    name: "One-Off Metric"
    criteria: "Special criteria for this eval only"
    threshold: 0.75
    evaluation_steps:
      - "Custom step"
```

## Framework Features

### Config-Driven Evaluation
- All evaluation settings in `config.yaml`
- Easy to modify without changing code

### Multiple Prompt Variations
- Test unlimited prompt variations
- Just add YAML files to `prompts/` directory

### Multi-Model Support
- Test different prompts on different models
- Configure models in `config.yaml`
- Override per prompt variation
- Compare performance across models

### Automatic Comparison
- Generates comparison summaries automatically
- Rankings by metric and overall
- Model information included in reports
- Markdown reports for easy reading

### Modular Architecture
- Shared framework code
- Feature-specific packages
- Reusable for image_prompt/ and image/ features

## Next Steps

1. **Resolve dependency conflict** using one of the options above

2. **Run initial evaluation**:
   ```bash
   poetry run pytest tests/prompt/caption/test_caption_evaluation.py -v -s
   ```

3. **Review results**:
   - Individual results: `tests/prompt/caption/results/prompt_v*_results.json`
   - Comparison: `tests/prompt/caption/results/comparison_report.md`

4. **Iterate on prompts**:
   - Modify existing prompts based on results
   - Add new variations
   - Re-run evaluation

5. **Expand to other features**:
   - Copy `caption/` structure for `image_prompt/`
   - Copy `caption/` structure for `image/`
   - Customize metrics for each feature

## Custom Metrics

Custom metrics should inherit from `deepeval.metrics.BaseMetric`:

```python
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class YourMetric(BaseMetric):
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> float:
        # Your evaluation logic
        self.score = calculated_score
        self.success = self.score >= self.threshold
        self.reason = "Explanation of score"
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Your Metric Name"
```

## Test Data Format

Campaign specifications in `data/campaign_specs.json`:

```json
[
  {
    "input_description": "Human-readable description",
    "event_name": "Event name",
    "company_name": "Company name",
    "industry": "Industry",
    "tone": "Tone (professional, friendly, etc.)",
    "event_tags": ["tag1", "tag2"],
    "context": [
      "Context item 1",
      "Context item 2"
    ]
  }
]
```

## Implementation Status

- ✅ Framework core components implemented
- ✅ Caption evaluation setup complete
- ✅ Three prompt variations created
- ✅ Custom metrics implemented
- ✅ Test runner created
- ⚠️ Dependencies need resolution (see above)
- ⬜ Image prompt evaluation (to be implemented)
- ⬜ Image generation evaluation (to be implemented)
