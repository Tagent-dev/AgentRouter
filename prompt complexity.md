The interesting part: don't just classify "prompt complexity"
- I would make your project much more sophisticated than:
```bash
short prompt → small model
long prompt → big model
```
- That won't work well enough for an enterprise product.
- Instead, your router should evaluate things like:
```
                    ┌─────────────────────┐
Prompt ────────────►│   Request Analyzer   │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ↓                 ↓                 ↓
          Complexity        Task Type       Context Size
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ↓
                    ┌─────────────────────┐
                    │   Model Router      │
                    └──────────┬──────────┘
                               ↓
             ┌─────────────────────────────────┐
             │ Model Capability + Cost +       │
             │ Latency + Context + Availability│
             └───────────────┬─────────────────┘
                             ↓
                    Best Model Selection
```
For example:

| Request                     | Routing                  |
| --------------------------- | ------------------------ |
| Fix typo                    | Cheap model              |
| Explain this function       | Small/medium             |
| Write a simple unit test    | Medium                   |
| Refactor a class            | Medium                   |
| Debug multi-file issue      | Strong model             |
| Architecture design         | Strong model             |
| Complex Kubernetes incident | Strong/reasoning model   |
| Large repository analysis   | Model with large context |
| Simple documentation        | Cheap model              |

And importantly, the router should consider what the model is good at, not just how powerful it is.
