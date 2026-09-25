# genealog-ia

**A research assistant for family history that finds the record, writes down what it actually says, and refuses to invent the rest.**

- **For anyone tracing a family**, from a first name on the back of a photograph to a parish register of 1643.
- **Covers the whole chain**, not just the search: find → read → record with its source → request the missing certificate → publish a page the family reads.
- **64 catalogued sources**, 45 French departmental portals on 15 platform engines, plus Italy, Algeria and 70 services across 12 regions of the world.
- **Built on a real corpus** of 754 people and 350 sources. Every rule in it cost something first.

---

## Install

```bash
claude plugin marketplace add pascalpediroda-maker/genealog-ia-plugin
claude plugin install genealog-ia@genealog-ia
```

Three questions on activation — where to file archives, where your photographs live, where to write the corpus. You never type a path again.

---

## Table of contents

- [The problem](#the-problem)
- [What it covers](#what-it-covers)
- [It does not only search](#it-does-not-only-search)
- [Why the rules read the way they do](#why-the-rules-read-the-way-they-do)
- [Requirements](#requirements)
- [Before you write to a town hall](#before-you-write-to-a-town-hall)
- [Status](#status)

---

## The problem

An AI that reads old handwriting is impressive for ten minutes and dangerous for years.

- It fills a blank with the plausible name, and a fabricated ancestor propagates through every tree that copies yours.
- It declares a register empty after a sweep that only ever showed one act in three.
- It states a conclusion from a partial reading, and the next session inherits a wall that was never there.

All three happened in the corpus this plugin was built on. The code is mostly there to stop them happening again.

---

## What it covers

| | |
|---|---|
| **France** | 45 departmental archive portals on 15 platform engines. Opening one more is usually configuration, not code |
| **Elsewhere** | Italian civil registers, Algerian civil registration, and a catalogue of 70 services across 12 regions — national archives, parish databases, war dead, migration indexes |
| **Besides registers** | conscription records, digitised press, the French national death index, cemetery and deportation databases |
| **Images** | half-page rendering at legible size, crop to the ink, zoom on a faint word, contact sheets that date a register without reading it |

---

## It does not only search

**It writes.** Five readable JSON files — people, unions, moments, places, sources. Every value carries its source and its confidence. One event reads differently depending on whose page you are on.

**It repairs.** The GEDCOM tooling fixed 3 trees exported by a Windows XP program: 5,234 people, 1,268 dates that had been sitting in the "place" field, 219 broken family links — without modifying a single original file.

**It does the paperwork.** Drafts the certificate requests, names the right town hall, and knows who is legally entitled to ask for what.

**It refuses to publish.** Checks that fail rather than warn: a date contradicting the person's record, a participant whose point of view nobody verified, an off-schema field that would display nowhere, two passages telling the same story twice.

---

## Why the rules read the way they do

A "Clotilde" lived in the founding corpus for days — record, parents, events — before anyone noticed she had been born of a first name invented by an automatic transcription.

A parish was declared empty on twelve years of registers; the marriage was there, third act on the page. The sweep used only ever shows the first act of each page, and nobody had written that down.

A margin sweep missed a birth because a 75-centime revenue stamp covered half the marginal note.

Each of those is now a rule, and several are scripts that fail. A bare rule is re-read and forgotten; a rule attached to its accident is remembered.

**The skills are written in French**, like the registers they open and the people reading them.

---

## Requirements

| | |
|---|---|
| **Claude Code** | with a model that can read handwritten register images |
| **Python 3.10+** | Pillow, numpy, certifi, truststore, PyMuPDF |
| **Node** | for 13 French departments only |

Simplest route to Python is [`uv`](https://docs.astral.sh/uv/), one binary that installs the interpreter and the dependencies itself:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh                  # macOS, Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"       # Windows
```

**About Node.** 13 departmental portals defend themselves with proof-of-work challenges and block non-browser clients. Those need a driven Chrome — Node and Playwright, ~300 MB. The other 32 departments, the image reading, the death index, the checks and the GEDCOM export work without it, and the message tells you on the day you need it.

---

## Before you write to a town hall

- **A French civil-registration certificate is free.** The sites charging €35 are not the administration, and they outrank the town hall in search results.
- **After 75 years it is the archive that opens, not the registry desk.** A third party never gets a full copy from a town hall, not even for a 1904 record — a direct descendant gets it in five minutes.

---

## Status

Version 0.1.0. In daily use on three family corpora. The skills are French; this README and the manifest are English.

MIT. The catalogue of holdings outside France is adapted from [`sliday/genealogy-research`](https://github.com/sliday/genealogy-research), same licence.
