# généalogie — search French archives, and never invent an ancestor

A Claude Code plugin for **French civil-registration and parish archives**: finding a
register, reading it at the right magnification, and writing what you actually read into a
family corpus.

> **The skills are in French, and that is deliberate.** They are written for the archives
> they open — French departmental portals, French access law, the spelling habits of a
> parish clerk. If you research French ancestors, this is for you. If you don't, the
> *method* may still interest you; the coverage will not.
>
> *[Lire ce README en français](README.fr.md).*

---

## What it does

**Search.** Sixty-three catalogued sources: **forty-five departmental archive portals**
running on fifteen different platform engines, Italian civil registers, Algerian civil
registration, military conscription records, digitised press, the French national death
index.

**Read a register.** One half-page per image at the size that is actually legible, cropped
to the ink; zoom on a faint word; contact sheets that date a register without reading it.
And the four sweeping methods, each with **what it cannot see** — a margin never shows a
marriage.

**Write.** A corpus where every fact carries its source and its confidence, where one event
reads differently depending on whose page you are on, and where sensitive material is
hidden **without being hidden silently**.

**Refuse.** Checks that fail: an event whose date contradicts the person's record, a
participant whose point of view nobody verified, an off-schema field that would display
nowhere, a moment with no date that would sort after the death, two passages telling the
same story twice.

---

## What it will not do

- **It never creates a person from an inference.** Named by a record or by a witness → the
  person is created. Inferred from a namesake, a plausible age, an OCR reading → not
  created; the question is asked instead.
- **It never fills a blank.** A word it could not read at magnification is written
  `[non lu]`.
- **It never concludes from a partial sweep.** A report states *by which method* a negative
  was obtained, because "swept the margins" and "read in full" are not the same claim.

Every one of these rules exists because the corpus it was built on paid for it. A
"Clotilde" lived in that tree for several days, with a record, relatives and events: she had
been born of a first name invented by an automatic transcription.

---

## Install

```bash
claude plugin marketplace add <repo>
claude plugin install genealogie
```

On activation you answer **three questions**: where to file downloaded archives, where your
family photographs already live, and where to write the corpus. You will never type a path
again — and you can change them later in `/config`.

### Requirements

| | |
|---|---|
| **Claude Code** | with a model able to read handwritten register images |
| **Python 3.10+** | five light dependencies: Pillow, numpy, certifi, truststore, PyMuPDF |
| **Node** | **for thirteen departments only** — see below |

The simplest way to get Python is **[`uv`](https://docs.astral.sh/uv/)**, a single binary
that installs the interpreter and the dependencies by itself:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"      # Windows
curl -LsSf https://astral.sh/uv/install.sh | sh                  # macOS, Linux
```

### About Node, plainly

Thirteen departmental portals defend themselves — proof-of-work challenges, blocking
non-browser clients. Reaching them needs a real driven Chrome, so **Node and Playwright,
around 300 MB**. The other thirty-two departments, the image reading, the death index, the
checks and the GEDCOM export do not need any of it.

**So you install none of that until your family turns out to be in one of those thirteen** —
and the message will tell you on the day it happens.

---

## What it produces

**Five readable JSON files**, on your disk. No database, no account, no platform.

And a checked **GEDCOM 5.5.1 export** that opens in Heredis, Gramps or Geneanet. The same
tooling repaired three trees exported by a Windows XP program: 5,234 people, 1,268 dates
that had been sitting in the "place" field, 219 family links restored — **without ever
modifying the original files**.

---

## Two things worth knowing before you write to a French town hall

- **A civil-registration certificate is free.** Always. The sites that charge thirty-five
  euros for one are not the administration, and they rank above the town hall in search
  results.
- **After seventy-five years it is the *archive* that opens, not the registry desk.** A
  third party never obtains a full copy from a town hall, not even for a 1904 record — but a
  direct descendant gets it in five minutes. Before building a case, work out who in the
  family has the right to ask.

---

## Licence

MIT. The worldwide catalogue of holdings outside France is adapted from
[`sliday/genealogy-research`](https://github.com/sliday/genealogy-research), under the same
licence.
