# Business Strategist Workflow

1. Normalize the request and inspect only the relevant active manifest.
2. Run `python3 scripts/route_workflow.py "<request>"`.
3. If the result is `business-strategist`, ask one routing question; otherwise dispatch the selected specialist.
4. Pass only the selected specialist's required inputs. Do not preload unrelated research or brand references.
5. Record the route, approvals, artifacts, and next action in the controller manifest. Specialist workers write disjoint artifacts and return result packets.

## Output

```json
{
  "skill": "<selected skill>",
  "mode": "<default or specialist mode>",
  "matched": [],
  "forbidden_skills": [],
  "approval_required": false,
  "next_action": "<concrete next step>"
}
```
