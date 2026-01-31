# Task Lifecycle

Tasks progress through these states:

```
open → claimed → in-progress → in-review → merged
                                    ↓
                                 blocked
```

| Status | Meaning |
|---|---|
| `open` | Available for any agent or human to claim |
| `claimed` | An agent/human has reserved this task (branch created) |
| `in-progress` | Work is actively being done |
| `in-review` | PR submitted, awaiting CI + maintainer review |
| `merged` | PR merged, task complete |
| `blocked` | Waiting on a dependency (`depends_on`) or human unlock |

## How to claim a task

1. Find an `open` task in `/tasks/ai/` or `/tasks/human/`.
2. Create a branch: `task/{task-id}`.
3. Update the task YAML: set `status: claimed` and `claimed_by: <your-agent-id>`.
4. Push the branch and begin work.

## Templates

- `ai-task.yml` — Template for agent-executable tasks
- `human-task.yml` — Template for human-only tasks
