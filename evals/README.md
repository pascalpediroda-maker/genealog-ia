# Evals

Five cases. Each runs three times **with** the plugin and three times **without**, and the
score that matters is the difference — a case that passes in both arms proves the plugin
had nothing to do with it.

```bash
claude plugin eval .                                   # the whole suite
claude plugin eval . --case <name> --runs 1 --ablation none   # one case, cheaply
```

| case | what it holds | why it exists |
|---|---|---|
| `declenchement-recherche` | a natural request for a marriage record fires `archives-fr`, and the reply proposes a real archival route | the skill is worthless if it does not fire on the way people actually write |
| `declenchement-ouvrir-son-arbre` | "I want to start my family tree" fires `nouveau-corpus` | **non-regression.** Until 25 September 2026 that skill's published description said *"a tree that is NOT their own"* — so it would not have fired on the first thing any new user types |
| `refus-de-deduire-une-personne` | a witness with the right surname and a plausible age is **not** turned into a parent | the founding corpus carried a person for days who had been born of an automatic transcription |
| `negatif-partiel-ne-conclut-pas` | a margin sweep that found no marriage does not license moving to the next parish | a margin sweep never shows a marriage — their text starts at the left edge. Concluding from it cost a real marriage |
| `non-declenchement-hors-sujet` | a plain Python question fires **no** skill | a skill that fires on everything is worse than one that fires on nothing |

## Two things to know before running

**It costs.** Each case is six model runs plus the judge calls — roughly $0.40 and 75
seconds per case, so this suite is about $2 and five minutes.

**It will not run on Windows natively.** `claude plugin eval` has no sandbox there, and a
case that grants `Bash` is refused. Run the suite in CI, where the environment is fixed and
the scores are steadier.

## Reading a result

```
CASE                            WITH  W/OUT Δ      RUNS COST
declenchement-ouvrir-son-arbre  1.00  0.33  +0.67  6    $0.41
```

`Δ` near zero with the `tool_used: Skill` grader failing means Claude is not choosing the
skill on natural phrasing. That is a `description` problem, not a content problem — fix the
frontmatter and run the case again.
