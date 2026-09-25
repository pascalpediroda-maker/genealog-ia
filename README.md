# genealog-ia

A Claude Code plugin for genealogy research: it finds the records, reads the handwriting, and writes what they say into a documented family history.

Claude already reads a document and writes a decent summary. Two things it does not do well on its own: **searching archives** — a hundred departmental portals, each defending itself differently — and **stopping at what it actually read**. Left alone it fills a blank with the plausible name, and a fabricated ancestor propagates into every tree that copies yours.

This plugin adds the missing half: the search tooling for **130+ online sources**, the reading method, and the reliability rules — each one written after it cost something on a real family tree.

---

## Skills

| Skill | What it does | Sample prompts |
| --- | --- | --- |
| **archives-fr** | Open an archive portal, find a register, pull its views, read an act at the right magnification, and record what was found — and what was not. | "find my great-grandfather's 1858 marriage, he was from the Haute-Loire", "list the registers for this commune", "read views 120 to 128", "did she die there after 1870?" |
| **trame-fr** | Write a testimony or an act into the corpus: people, unions, moments, sources. Draft the narrative, decide what stays private, check a page before publishing. | "add this act to the corpus", "write her life from these three sources", "should this stay private?", "check his page before I publish" |
| **nouveau-corpus** | Open a tree for someone else — a friend, a club member — from a photograph, a PDF, a GEDCOM or a spoken memory. | "start a corpus for this family", "here is a scanned hand-drawn tree", "what should I ask them next?" |

---

## Proven in use

Three family corpora run on it daily. The first was built in **six weeks, from no prior knowledge of genealogy**: 754 people, 482 life moments, 350 sources, 258 photographs.

| | |
|---|---|
| **11 generations** | in under 4 hours, from nothing back to a founder born in 1632 |
| **≈ 400 views / hour** | sweeping old registers, even with no decennial index |
| **31,356,377 rows** | 6.27 GB scanned in 6 minutes to find a woman whose date of birth was all that was known |
| **3 GEDCOM files repaired** | exported by a Windows XP program that had written every unparsed date into the *place* field — 5,234 people, 1,268 dates and 219 family links put back, no original file touched |
| **22 certificate requests** | drafted, addressed, and tracked |

And three photographs that had no caption: a scrap of film poster dated one to autumn 1958, through the film's release schedule. A prisoner number and camp name on the back of another — Stalag II B, Pomerania. A photographer's stamp on a third — *E. Bernauer, Troisdorf* — which put it in occupied Germany and opened a conscription-record search.

**None of those three facts was known to the family.**

---

## Install

```bash
claude plugin marketplace add pascalpediroda-maker/genealog-ia-plugin
claude plugin install genealog-ia@genealog-ia
```

Three questions on activation — where to file archives, where your photographs already live, where to write the corpus. You never type a path again.

| Requirement | |
|---|---|
| **Claude Code** | with a model that can read handwritten register images |
| **Python 3.10+** | installed for you by [`uv`](https://docs.astral.sh/uv/) if you do not have it |
| **Node** | for about a dozen French departments whose portals block non-browser clients. You are told on the day you need it |

---

## Where it reaches

| | |
|---|---|
| **France** | nearly half the departments, on the dozen-odd platforms their portals run on. Opening one more is usually configuration, not code |
| **Elsewhere** | Italian civil registers, Algerian civil registration, and a catalogue running from Poland to Argentina |
| **Besides registers** | conscription records, digitised press, the national death index, cemetery and deportation databases |
| **Images** | half-page rendering at legible size, crop to the ink, zoom on a faint word, contact sheets that date a register without reading it |

---

## The reliability rules

They are not advice in a document. Several are scripts that fail rather than warn.

- **`[non lu]` instead of the plausible name**, wherever a word could not be read at magnification.
- **A negative states its method.** "Swept the margins" and "read in full" are not the same claim — a margin sweep never shows a marriage.
- **No person is created from a resemblance.** Named in a record or by a witness → created. Inferred from a namesake or a plausible age → the question comes back to you.
- **Every value carries its source and its confidence**, and a losing reading is kept beside the winning one with the reason.
- **Publication is refused** when a check fails: a date contradicting the person's record, a moment with no date that would sort after the death, two passages telling the same story twice.

Each came from an accident. A "Clotilde" lived in the founding corpus for days — record, parents, events — before anyone noticed she had been born of a first name invented by an automatic transcription.

---

**The skills are written in French**, like the registers they open. *[Lire ce README en français](README.fr.md).*

MIT. The catalogue of holdings outside France is adapted from [`sliday/genealogy-research`](https://github.com/sliday/genealogy-research), same licence.
