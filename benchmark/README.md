# Benchmark

Model benchmarking feeds capability scores into the model registry. Scores
are measured, never invented.

## Domains

```text
datasets/coding/        Code generation and completion tasks
datasets/debugging/     Fault localization and root-cause tasks
datasets/refactoring/   Structural change tasks
datasets/kubernetes/    Cluster, manifest and incident tasks
datasets/terraform/     Infrastructure-as-code tasks
datasets/sql/           Query and schema tasks
datasets/architecture/  System design tasks
datasets/security/      Security review and hardening tasks
```

## Measured per model and domain

```text
quality
success rate
cost
latency
context handling
tool usage
```

## Layout

```text
datasets/    task datasets per domain
runners/     benchmark execution
evaluators/  scoring of model output
reports/     generated benchmark reports
```

## Status

Scaffold. No datasets or runners yet.
