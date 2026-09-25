# genealog-ia

## Eleven generations in one afternoon. Not one invented ancestor.

The afternoon is measured: a branch went from nothing to a founder born in 1632, between 3 p.m. and 7 p.m. on a Saturday. The second half of that sentence is the hard one, and it is what most of this code is for.

```bash
claude plugin marketplace add pascalpediroda-maker/genealog-ia-plugin
claude plugin install genealog-ia@genealog-ia
```

---

## You already know what goes wrong

You ask an AI to read a parish register. It is impressive for ten minutes.

Then it fills a blank with the name that *fits*. It tells you a register holds nothing, after a sweep that only ever showed one act in three. It states a conclusion from half a reading — and six months later you are still working around a wall that was never there.

One fabricated ancestor does not stay yours. It propagates into every tree that copies yours.

**All three happened on the family tree this plugin was built on.** They are why it exists.

---

## What it does instead

**It writes `[non lu]`** where it could not read the word, instead of the plausible name.

**It tells you how it looked.** "Swept the margins" and "read in full" are not the same claim, and the report says which — because a margin sweep never shows a marriage, and nobody had written that down before it cost a marriage.

**It will not create a person from a resemblance.** Named in a record or by a witness → created. Inferred from a namesake or a plausible age → the question comes back to you.

**And it refuses to publish** when a check fails: a date that contradicts the person's record, a moment with no date that would sort after the death, two passages telling the same story twice.

---

## What you get out of it

**Walls fall by the side door.** An ancestor nobody could find for years: death indexes only carry maiden names, censuses list wives under the husband's. She was invisible from both sides. The line that broke it was her mother-in-law's, two rows down in the same household.

**Photographs date themselves.** A photographer's stamp read under magnification put a family portrait in occupied Germany. A scrap of film poster behind two children narrowed a picture to one autumn, through the release schedule of the film.

**A page the family actually opens.** Not a tree diagram — a life told moment by moment, with the record image under the text, and every fact carrying where it came from and how sure you are.

**The paperwork, written.** The certificate requests drafted, the right town hall named, and who is legally entitled to ask for what — which in France is the difference between five minutes and never.

---

## Where it reaches

| | |
|---|---|
| **France** | nearly half the departments, on the dozen-odd platforms their portals run on. Opening one more is usually configuration, not code |
| **Elsewhere** | Italian civil registers, Algerian civil registration, and a catalogue running from Poland to Argentina |
| **Besides registers** | conscription records, digitised press, the national death index, cemetery and deportation databases |
| **Images** | half-page rendering at legible size, crop to the ink, zoom on a faint word, contact sheets that date a register without reading it |

It also repairs what other software broke: three trees exported by a Windows XP program, where every date it could not parse had been written into the *place* field. Thousands of people put back in order, and not one original file touched.

---

## Install

```bash
claude plugin marketplace add pascalpediroda-maker/genealog-ia-plugin
claude plugin install genealog-ia@genealog-ia
```

Three questions on activation — where to file archives, where your photographs already live, where to write the corpus. You never type a path again.

| | |
|---|---|
| **Claude Code** | with a model that can read handwritten register images |
| **Python 3.10+** | installed for you by [`uv`](https://docs.astral.sh/uv/) if you do not have it |
| **Node** | for about a dozen French departments whose portals block non-browser clients. You will be told on the day you need it |

---

## Where the rules come from

A "Clotilde" lived in the founding corpus for days — record, parents, events — before anyone noticed she had been born of a first name invented by an automatic transcription.

A parish was declared empty across twelve years of registers. The marriage was there, third act on the page.

A margin sweep missed a birth because a 75-centime revenue stamp covered half the marginal note.

Each of those is now a rule, and several are scripts that fail rather than warn. A bare rule is re-read and forgotten; a rule attached to its accident is remembered.

**The skills are written in French**, like the registers they open and the people reading them. *[Lire en français](README.fr.md).*

---

MIT. The catalogue of holdings outside France is adapted from [`sliday/genealogy-research`](https://github.com/sliday/genealogy-research), same licence.
