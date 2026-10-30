# Paper Review Lab

A buildless GitHub Pages site with an evidence-backed manuscript workbench,
24 anchored criteria, four contribution profiles, aggressive scoring, and a
searchable collection of 300 historical citation records from 2018–2022.

Serve this folder over HTTP; opening `index.html` as a local file prevents JSON
fetches in many browsers:

```sh
python -m http.server 8765 --directory docs
```

Open `http://localhost:8765`. All CSS, JavaScript and data files are local to the
site. Assessment entries and imported JSON remain in the tab; export before
closing it. The website does not read manuscripts or call an AI service.

## Verification

From the repository root, Python 3.10+ runs the portable toolkit checks:

```sh
python -m unittest discover -s toolkit/validation -p 'test_*.py' -q
python tests/check_site_parity.py
```

The parity check also needs Node.js 20+ and compares 176 fictional scenarios
against the bundled four integer-weight profiles. It covers raw/effective scores,
domain results, coverage, readiness, caps and policy/rubric fingerprints. Custom
floating-point rubric serialization is outside this browser compatibility claim.
Domain thresholds use unrounded ratios; displayed scores use two-decimal rounding.

## Publication and provenance

GitHub Pages serves `main:/docs` with `.nojekyll`; no package build or external
scripts are needed. Keep `data/manuscript-rubric.json` and
`data/scoring-policies.json` identical to their toolkit assets.

`data/corpus.json` includes citation metadata only. The original local collection
contained 300 abstracts and 238 downloaded bodies; neither is hosted here.
Collection is distinct from reading or scientific validation. Eighteen selected
papers were inspected at abstract or selected-section level; no claim of 300
complete scientific reviews is made. These are explicitly selected venues, not
an objective venue ranking or a representative paper sample.

`data/demo-assessment.json` contains fictional ratings and evidence to illustrate
arithmetic. It is not a real-paper assessment. Aggressive thresholds are original
editorial conventions with no prospective real-manuscript calibration; scores
are not acceptance predictions or scientific certification.
