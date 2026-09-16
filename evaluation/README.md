# Evaluation

Measures whether the router is making good decisions, which is a different
question from how good a given model is.

## Tracked metrics

```text
routing accuracy
successful completion rate
cost savings
quality loss
latency
fallback rate
escalation rate
```

The headline objective: cost reduction without unacceptable quality degradation.

## Regression dataset shape

```text
prompt
task_type
complexity
required_capabilities
candidate_models
expected_best_model
actual_selected_model
cost
quality
latency
```

## Layout

```text
routing/      routing decision evaluation
quality/      output quality evaluation
cost/         cost outcome evaluation
latency/      latency outcome evaluation
reliability/  fallback and failure behaviour evaluation
```

## Status

Scaffold, not implemented.
