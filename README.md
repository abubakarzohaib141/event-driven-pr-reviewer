# #6 — Event-Driven PR Reviewer

A repository that automatically reviews its own Pull Requests. No one asks
Claude to review a PR — a real GitHub `pull_request` webhook event fires
a Claude Code **Routine**, which independently inspects the diff, runs the
tests, reasons about correctness, and posts a review to GitHub.

```text
PR opened / pushed
       |
GitHub pull_request webhook event
       |
Claude Code Routine fires automatically
       |
Reviewer inspects diff + full source + runs tests
       |
Reviewer posts a review to the PR
```

## 1. What this assignment teaches

The difference between an **event-driven trigger** and something you have
to remember to invoke. In Assignments #1–#5, *I* (the human, via the
assistant) always decided when a process ran — start the watcher, run the
retry loop, run the workflow batch. Here, nothing I do inside a chat
session starts the review. **GitHub itself, via a webhook event, is what
starts it.** The review happens whether or not anyone is watching.

## 2. What an event-driven loop means here

A Claude Code **Routine** is a persistent cloud configuration (not a
one-off chat session) that can be bound to an event source instead of
only a cron schedule. This project attaches a **GitHub webhook trigger**
to a routine: every `pull_request` event on the repo is delivered to
Anthropic's infrastructure, which spins up a fresh, isolated Claude Code
session, hands it the event's context (which PR, which commit, which
action), and lets it act — with GitHub write access to post a real review.

## 3. What GitHub event triggers the reviewer

`pull_request.opened` and `pull_request.synchronize` (a new commit pushed
to an existing PR's branch), via a webhook trigger created on the routine:

```json
{
  "source": "github",
  "hook_type": "app",
  "scope_id": "github.com/abubakarzohaib141/event-driven-pr-reviewer",
  "events": ["pull_request.opened", "pull_request.synchronize"]
}
```

Routine: https://claude.ai/code/routines/trig_01UvP3AFju5TfNbizszJhTQH

## 4. The planted bug

`src/inventory.py`, `has_enough_stock()`. On `main` it's:

```python
return available >= requested
```

PR #1 changes it to:

```python
return available > requested
```

...inside a commit described as "simplify the comparison," alongside a
genuinely correct new function (`low_stock_warning`). The docstring says
the function returns whether `available` units "can satisfy" a request
for `requested` units — at exact equality (`available == requested`),
the request *can* be satisfied, so the correct answer is `True`. The
bug flips that boundary case to `False`, silently breaking
`remaining_after_order()` too (it starts raising instead of returning
`0` when stock exactly matches the order). Two pre-existing tests catch
it: `test_has_enough_stock_true_when_exactly_equal`,
`test_remaining_after_order_exact_match_leaves_zero`.

## 5. The PRs

- **PR #1** (the real bug): https://github.com/abubakarzohaib141/event-driven-pr-reviewer/pull/1
- **PR #2** (trivial, opened purely to capture clean `opened`-event evidence — see §9): https://github.com/abubakarzohaib141/event-driven-pr-reviewer/pull/2

## 6–9. Evidence — what actually happened (including the troubleshooting)

Being transparent about the real timeline, because it's part of the
lesson: the first webhook trigger I created used the event name
`"pull_request"` (bare, no action suffix). PR #1 was opened
(`07:35:24 UTC`) and pushed to twice more (`07:38:57`, `08:07:23`) — zero
automatic runs. I confirmed via the API that the GitHub App was
installed correctly ("All repositories") and the routine itself worked
perfectly when manually fired (`RemoteTrigger action: run` at
`08:15:48` — clearly a **diagnostic only**, explicitly not claimed as
assignment evidence, but useful proof the routine's logic was sound).
One more push (`08:36:38`) — still nothing automatic.

**The fix:** re-registering the webhook trigger using fully-qualified
event names — `"pull_request.opened"` and `"pull_request.synchronize"` —
instead of the bare `"pull_request"` string. The very next push fired the
routine automatically within 2 seconds.

### Evidence: synchronize event → automatic review (PR #1, the real bug)

Pushed a commit to PR #1's branch at `10:23:04 UTC`. A new session
(`cse_011nbe8xFrrCRYhD1CBm1req`) was created automatically at
`10:23:06 UTC` — **2 seconds later, with no manual trigger call.** Its
log begins with GitHub's own injected context:

```
<github-trigger-context>
This routine was triggered by a GitHub webhook.
Event: pull_request.synchronize
Repository: abubakarzohaib141/event-driven-pr-reviewer
PR: #1
Branch: feature/low-stock-warning -> main
Head SHA: a57e838d0b298a18b4a097ee2ccdfcf2c8b3ae93
</github-trigger-context>
```

`a57e838` is exactly the commit I had just pushed. The session then:
fetched the PR, read the full diff and complete file contents, installed
pytest and ran the real suite (`2 failed`), and posted a review
identifying the exact bug — line, root cause, concrete failing input
(`has_enough_stock(5, 5)` now `False`), the two failing tests, and the
downstream impact on `remaining_after_order`. GitHub blocked a formal
`REQUEST_CHANGES` verdict ("Can not request changes on your own pull
request" — the reviewing identity and the PR author are the same
account), so it adapted and posted the full verdict as a clearly-labeled
comment review instead. Visible at:
https://github.com/abubakarzohaib141/event-driven-pr-reviewer/pull/1

### Evidence: opened event → automatic review (PR #2, clean test)

PR #1's original `opened` event predated the trigger fix, so to get
unambiguous evidence for `opened` specifically, I opened a second,
trivial PR (`#2`, a 2-line README comment, no code) at `10:26:06 UTC`. A
new session (`cse_018CTXHragAXqDpied7nVR9v`) fired automatically at
`10:26:08 UTC` — again 2 seconds later. Its injected context:

```
Event: pull_request.opened
PR: #2
Head SHA: 4ce7b1c13a01293cd4f878aa4dcfa50f2b59fe34
```

It correctly reasoned that a 2-line HTML comment has no logic or test
surface worth flagging, and posted a review saying so (again as a
comment, since GitHub also blocks self-approval) rather than inventing a
problem to seem thorough. That distinction matters: the reviewer isn't
just pattern-matching "always find something."

## 10. Why the GitHub event acts as the heartbeat

There is no cron schedule driving this (the routine's `cron_expression`
is a required-but-irrelevant daily placeholder — the routine framework
requires *some* schedule field even for a purely event-driven routine).
The actual pulse is GitHub itself: every `pull_request` action becomes a
webhook delivery, which becomes a routine fire, which becomes a fresh,
isolated review session. No polling, no manual re-invocation — the event
*is* the trigger, exactly like Assignment #4's reviewer was triggered by
me running a script, except here the "script" is GitHub's own event
delivery.

## 11. How this differs from Assignments #1–#5

| # | Trigger |
|---|---|
| 1 | A human runs a watcher loop that polls a file every N seconds |
| 2 | A human runs a retry loop that polls a test command |
| 3 | A human re-runs a script that reads/writes `progress.md` |
| 4 | A human runs the reviewer script against a worktree |
| 5 | A human runs one orchestrating command for a batch |
| **6** | **GitHub fires the reviewer — no human invocation at all** |

#1–#5 all demonstrate different *engines* that still need a human (or a
cron job) to press "go." #6 is the first one where the triggering event
comes from outside the assistant/human loop entirely.

## 12–13. If the reviewer misses the bug

The designed mechanism (not needed here, since the reviewer caught the
bug on both the diagnostic and the genuine automatic run, but documented
per the assignment): if a review came back too soft, the fix is to
tighten `reviewer_prompt` inside the routine's `job_config` (via
`RemoteTrigger action: update`) — e.g. adding more explicit instructions
not to trust green tests, or to check specific classes of bugs — then
push another commit to the open PR. That push fires a fresh
`pull_request.synchronize` event, which fires the routine again with the
updated prompt, against the current diff. No manual re-invocation is
needed for the retry either — the same event mechanism that fired the
first review fires the corrected one.

## Final conceptual architecture

```text
GitHub pull_request event (opened / synchronize)
       |
   webhook delivery (GitHub App)
       |
Claude Code Routine (trig_01UvP3AFju5TfNbizszJhTQH)
       |
fresh isolated session: clone repo, read diff + full files, run tests
       |
independent reasoning about correctness (not just "tests passed")
       |
review posted to the PR on GitHub
```
