# Asking sharp clarifying questions

The brainstorm phase gets **one round** of questions. Make them count. The goal is to remove the
ambiguity that would otherwise cause a wrong plan — not to interrogate the user.

## What to ask about (in priority order)

1. **Observable behavior.** What should be true for the user/system when this is done? Concrete examples
   beat abstractions: "what happens when a logged-out user hits this page?"
2. **Boundaries / non-goals.** What is explicitly *not* part of this? The cheapest scope control there is.
3. **Hard constraints.** Deadline, performance budget, backwards-compat, must-reuse-X, regulatory.
4. **The undecided fork.** If there's a real design fork (sync vs async, new table vs reuse, build vs
   buy), surface it now — it's the difference between one plan and another.

## What *not* to ask

- Anything `repo-map.md` or `constitution.md` already answers (stack, test framework, style). Read first.
- Anything with an obvious sensible default — state the default instead and let the user override.
- Five questions when two would do. If you're padding, you don't understand the goal yet.

## Form

- Prefer concrete multiple-choice over open-ended when the options are knowable — it's faster for the user
  and surfaces the tradeoff. (Use the AskUserQuestion tool.)
- One decision per question. Bundling two forks into one question muddies the answer.
- Lead with a recommendation when you have one ("I'd default to X because…, ok?"). A decided user answers
  in one word.

## Smell test

A good question, answered either way, changes the plan. If both answers lead to the same plan, don't ask
it — just proceed.
