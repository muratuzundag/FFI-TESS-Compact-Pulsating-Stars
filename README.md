# FFI TESS Compact pulsating stars

![FFI TESS Compact pulsating stars](assets/FFI_TESS_banner.png)

Check whether TESS full-frame-image (FFI) coverage is returned for a target, extract custom-aperture photometry with **eleanor**, apply an explicit systematics-correction choice, and compute Lomb–Scargle spectra for variability searches.

This is the FFI companion to the USC/SC light-curve workflow. It analyzes FFIs rather than downloading existing SPOC 20-s/120-s target light curves.

> **Status: 0.1.0 release candidate.** Dependency-light, mocked-adapter and mocked-coverage tests passed. Live MAST/TIC/TessCut access, a full extraction installation, and real eleanor extraction were **not** tested in the generation environment. Complete [VALIDATION.md](VALIDATION.md) before calling the tool a stable, scientifically validated release.

| Component | Name |
|---|---|
| Repository | `FFI-TESS-Compact-Pulsating-Stars` |
| Distribution | `ffi-tess-compact` |
| Python module | `ffi_tess` |
| Terminal command | `ffi-tess` |

## Contents

- [What the tool does](#what-the-tool-does)
- [Install](#install)
- [Quick start](#quick-start)
- [Coverage is not extraction success](#coverage-is-not-extraction-success)
- [Apertures and corrections](#apertures-and-corrections)
- [Cadence and variability limits](#cadence-and-variability-limits)
- [Periodograms and candidate signals](#periodograms-and-candidate-signals)
- [Outputs and uncertainty conventions](#outputs-and-uncertainty-conventions)
- [Command-line options](#command-line-options)
- [Troubleshooting](#troubleshooting)
- [Reproducibility and validation](#reproducibility-and-validation)
- [Credits and licensing](#credits-and-licensing)

## What the tool does

1. Accepts a TIC ID or ICRS coordinates in decimal degrees.
2. Resolves TIC IDs to catalog coordinates when needed.
3. Queries **TessCut sky-position coverage**, returning sector, camera and CCD information.
4. By default, saves an inventory only: no eleanor installation or pixel download is needed for this stage.
5. With `--extract`, attempts every requested covered sector using `eleanor.Source(..., tc=True)` and `eleanor.TargetData`.
6. Applies a fixed circular or supplied-mask aperture, or explicitly requested upstream automatic aperture selection.
7. Recomputes systematics corrections after a custom aperture change, retaining raw photometry for comparison.
8. Saves per-sector light curves, spectra, candidate single-frequency fits, aperture masks, extraction arrays, figures and provenance.

This is a custom **wrapper/profile around upstream eleanor**, not a modified eleanor fork or an endorsed upstream release. It is intended to support compact-star work, but signal-preservation performance must be validated for your targets.

The tool does **not** identify pulsation modes, guarantee detection of faint stars, eliminate all systematics, separate blended sources automatically, or establish that a periodogram peak belongs to the requested star.

## Install

Python 3.10+ is required. Open a terminal in the extracted repository directory containing `pyproject.toml`.

### Coverage inventory only

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
ffi-tess --help
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

### Enable eleanor extraction

```bash
python -m pip install ".[extract]"
```

This installs eleanor separately. Follow the [upstream installation guidance](https://github.com/afeinstein20/eleanor) if its dependencies conflict with your environment. A clean environment is strongly preferred. The repository does not vendor upstream source or guarantee compatibility with every later release.

If `ffi-tess` is not on your executable path, use `python -m ffi_tess` in the same environment.

Internet is needed for initial dependencies, catalog/coverage queries, TessCut cutouts and auxiliary eleanor data. The tool does not imply a PyPI release already exists; install the supplied local source directory as above.

## Quick start

### 1. Ask whether coverage is returned

```bash
ffi-tess --tic 422526868 --output results_inventory
```

The TIC is a usage example, not a promise of specific data or successful extraction. The default run inventories coverage only and saves `ffi_coverage.csv` plus `manifest.json`.

### 2. Extract covered sectors

```bash
ffi-tess --tic 422526868 --extract --output results_extraction
```

All covered sectors are attempted independently. The default aperture is a fixed 1.5-pixel-radius circle centered on eleanor's inferred target position. Standard eleanor correction is selected; PCA and extra sigma clipping are not enabled by default.

### 3. Restrict the sectors

```bash
ffi-tess --tic 422526868 --extract --sectors 42 --output results_sector42
```

Replace the sector after reviewing the inventory. A requested sector absent from the coverage response is reported rather than silently substituted.

### 4. Use coordinates

Replace the placeholders with numerical ICRS RA and declination in decimal degrees:

```bash
ffi-tess --ra YOUR_RA_DEG --dec YOUR_DEC_DEG --output results_position
```

Add `--extract` to attempt photometry. The inventory is made at the supplied sky position; it does not require a target-name entry in an FFI catalog. During extraction, upstream eleanor may still require ancillary catalog metadata and can fail on a faint or uncataloged coordinate target. Such a failure does **not** mean coverage is absent.

For high-proper-motion stars, examine the difference between catalog/input positions and the position in each observing sector. This wrapper does not propagate proper motion to sector epochs automatically.

## Coverage is not extraction success

FFIs are detector images, not individual target-named light curves. This tool therefore does **not** infer FFI availability from an observation ID containing `ffi` or `lc`. It queries TessCut by sky coordinates.

| Manifest status | Interpretation |
|---|---|
| `coverage_found` | TessCut returned at least one sector/camera/CCD footprint for the position |
| `no_coverage_returned` | A successful query returned no footprint at query time |
| `query_failed_availability_unknown` | The service/query failed; availability is unknown |
| `target_resolution_failed` | TIC-to-coordinate resolution failed; availability was not determined |
| `not_queried` | Query has not been completed |

A footprint result does not guarantee usable pixels, acceptable quality, sufficient signal-to-noise, target detectability, or a successful eleanor extraction. Service coverage, data-release latency, detector boundaries and upstream compatibility can also affect the outcome.

Extraction/analysis success is recorded separately as `extracted_and_analyzed`. Failures retain positive coverage and an explanatory error; they are not relabeled “no FFI.” A sector covered by multiple detector rows is skipped for manual review rather than silently selecting a camera.

## Apertures and corrections

### Fixed circular aperture: default

```bash
ffi-tess --tic 422526868 --extract --aperture circle --radius 1.5
```

The mask includes pixels whose **centers** fall inside the requested radius. It is binary, not an exact fractional-pixel circular integration. The center defaults to eleanor's inferred `tpf_star_x`, `tpf_star_y`; use `--center X Y` only after inspecting the stamp. Coordinates are zero-based TPF column/row positions, not sky or full-CCD coordinates.

The aperture must fit inside the TPF; enlarge `--height`, `--width`, and the containing cutout if necessary. A fixed aperture avoids selecting an aperture solely because it minimizes observed scatter, but it is **not** guaranteed optimal for pulsations, crowding, saturation or photon noise. Compare multiple physically justified masks and inspect contamination.

### Supply a mask

```bash
ffi-tess --tic 422526868 --extract --aperture mask --mask aperture.npy
```

The `.npy` array must have shape `(height, width)`, contain finite weights in `[0,1]`, and have positive total weight. It is loaded with pickling disabled. The same mask argument is used for all requested sectors: do not assume a mask is correctly centered/oriented in every sector. Run sectors separately when different masks are required.

### Upstream automatic aperture selection

```bash
ffi-tess --tic 422526868 --extract --aperture auto --aperture-mode small
```

Available upstream modes are `normal`, `small`, `large`, and `all`. The mode also controls eleanor's initial internal aperture processing before a custom aperture is applied. Automatic low-scatter optimization is not the same as preservation of intrinsic variability, especially in blended or saturated fields.

### Correction choices

| Choice | Behavior |
|---|---|
| `--correction standard` | Default: use explicit eleanor `corrected_flux(..., pca=False)` after aperture selection |
| `--correction pca` | Use explicit `corrected_flux(..., pca=True, modes=N)`; `--pca-modes` defaults to 3 |
| `--correction none` | Analyze the raw aperture series; standard correction is still computed and exported for comparison |

Raw, standard-corrected and selected photometry are retained. PCA arrays are populated only when PCA is requested; otherwise they contain NaN as a clear “not computed” marker. `none` disables selecting a correction, not eleanor's initial internal TargetData processing.

Corrections regress against instrumental/ancillary information according to upstream behavior. Real stellar variability correlated with those regressors can be attenuated or altered. The wrapper does not remove all systematics or guarantee pulsation preservation. Inspect raw/corrected spectra and amplitudes, field neighbors, centroids and pixel images, and perform appropriate signal-preservation tests.

No extra polynomial flattening, smoothing or sigma clipping is applied by default. `--sigma VALUE` enables one-pass median/MAD clipping of the selected series; it can remove genuine excursions and should be justified for the science case. The default retained quality is **eleanor `quality == 0`**, not a generic SPOC short-cadence mask. `--keep-flagged` disables that quality exclusion and is a diagnostic option, not a recommendation.

## Cadence and variability limits

TESS FFI sampling changed during the mission. Typical reference values are:

| FFI cadence | Cadence-based Nyquist | Cycles/day |
|---|---:|---:|
| 1800 s / 30 min | 277.78 microhertz | 24 |
| 600 s / 10 min | 833.33 microhertz | 72 |
| 200 s | 2500 microhertz | 216 |

See [NASA's TESS product documentation](https://heasarc.gsfc.nasa.gov/docs/tess/data-products.html). The wrapper **measures the median positive timestamp spacing** of each extracted sector rather than hard-coding a cadence from its number. Missing samples can bias that estimate; inspect the reported cadence and original product metadata. Sampling interval is not automatically identical to effective exposure time.

The default lower frequency is 1/baseline; the default upper frequency is 0.99 times the cadence-based Nyquist. `--fmin` and `--fmax` are in microhertz. `--super-nyquist` allows a higher bound but does not resolve aliases or recover attenuated signals.

Fast compact-star pulsations may be aliased or strongly suppressed in FFIs. FFI coverage is not evidence that the target's expected pulsations are detectable. Use the companion USC/SC tool when suitable 20-s/120-s data exist.

Finite integration reduces a sinusoid's amplitude approximately by:

```math
R=\left|\frac{\sin(\pi f\Delta t)}{\pi f\Delta t}\right|.
```

Here `f` is in cycles/second and `Delta t` is effective integration time in seconds. This idealized expression is explanatory only: the wrapper applies **no automatic integration-time correction**, and cadence should not be substituted for integration time without checking the product. Barycentric timing and gaps also mean the cadence-based Nyquist is a reference scale, not an exact theorem for every inference.

## Periodograms and candidate signals

The code uses `astropy.timeseries.LombScargle` with a floating mean, one sinusoidal term, **unweighted standard power**, and the fast calculation method. It converts microhertz to cycles/second and uses relative times in seconds internally. Unlike SciPy's angular-frequency API, Astropy's frequency arguments are cycles per unit time.

Raw and selected curves are analyzed on the same evenly spaced grid. Oversampling samples peaks more finely; it does not improve independent frequency resolution. `--max-bins` guards against very large calculations.

Up to `--top-peaks` local maxima are listed as **candidates**, excluding boundary grid points. Each is refitted with a single-frequency sine/cosine model to report its amplitude in ppt, and the raw-series amplitude is evaluated at the same frequency for comparison. These fits are not jointly optimized, prewhitened, contamination-corrected or assigned formal amplitude/frequency errors.

`standard` LS power is dimensionless and normalized relative to each series' variance. Thus similar normalized powers before and after correction do **not** establish preserved physical amplitude. Inspect the candidate amplitudes and raw photometry as well.

There is **no automatic detection decision**, false-alarm line, local noise estimate, prewhitening, spectral-window analysis, or mode identification. A percentile of the observed power distribution is not labeled a false-alarm probability. Robust significance must account for the actual sampling, searched frequencies, systematics and noise model; see the [Astropy Lomb–Scargle guide](https://docs.astropy.org/en/stable/timeseries/lombscargle.html).

This is a Lomb–Scargle variability-search spectrum, not an FFT of interpolated gapped observations. Sectors are kept separate; this release does not create or mislabel a last-sector array as an all-sector merged light curve.

## Outputs and uncertainty conventions

Outputs are under `results/TIC_<id>/`, or an RA/Dec-based directory for coordinate input.

```text
TIC_<id>/
├── ffi_coverage.csv
├── manifest.json
├── s<sector>_lc.csv
├── s<sector>_lsp.csv
├── s<sector>_candidates.csv
├── s<sector>_aperture.npy
├── s<sector>_extraction.npz
├── s<sector>_metadata.json
└── s<sector>_diagnostics.png
```

| File | Meaning |
|---|---|
| `ffi_coverage.csv` | Returned sector, camera and CCD inventory |
| `manifest.json` | UTC timestamps, input, versions, coverage status, successful products and errors |
| `*_lc.csv` | Full BJD_TDB, BTJD, raw/standard/selected relative flux in ppt, raw-flux error in ppt, quality |
| `*_lsp.csv` | Frequency in microhertz and cycles/day, selected and raw LS standard power |
| `*_candidates.csv` | Candidate frequencies/periods/powers, selected/raw single-frequency amplitudes and candidate-only label |
| `*_aperture.npy` | Used pixel-weight mask |
| `*_extraction.npz` | Full returned timestamps/flux arrays, quality, raw errors, median image, aperture, and retained-row mask |
| `*_metadata.json` | Cadence estimate, baseline, normalization factors, frequency range, correction and pixel-weight count |
| `*_diagnostics.png` | Median image/aperture, raw/selected light curves and raw/selected spectra |

The exported time convention is **eleanor BTJD**, with `BJD_TDB = BTJD + 2457000`, following upstream documentation. No second barycentric correction is applied. This convention must be checked against actual extracted FITS timing metadata during live validation.

Flux normalization is `(flux/median - 1) * 1000`, independently for raw, standard and selected arrays on the common retained timestamps. One ppt is relative flux 0.001. The normalization factors are saved.

**Error warning:** upstream `flux_err` estimates uncertainty on **raw aperture flux**. The CSV `raw_flux_err_ppt` scales that quantity by the raw median only. It is **not** a valid full covariance or formally propagated error for corrected/PCA photometry. The code does not fabricate corrected errors or use this proxy as LS weights. Invalid raw error entries can remain NaN; photometry is not discarded solely to force a complete error column.

The extraction NPZ permits reanalysis but is not a complete original FITS/header/TPF cache. Original cutouts, auxiliary files and models remain managed by eleanor's cache, commonly under `~/.eleanor`. Retain them and the environment for reproducibility. This release does not claim a complete per-cadence inventory of original FFI product URLs.

A failed sector can leave intermediate files; the manifest, not file existence alone, determines success. Use a **new output directory for every distinct run**. Existing filenames can be overwritten and stale files are not automatically deleted.

Exit codes: `0` for completed inventory/processing without recorded errors, `1` for resolution/query/fatal failures, `2` for coverage-positive runs with extraction/selection/analysis errors. A successful empty inventory returns `0` with `no_coverage_returned` in the manifest; it is not an extraction success.

## Command-line options

| Option | Default | Meaning |
|---|---|---|
| `--tic ID` | Input alternative | TIC identifier |
| `--ra DEG --dec DEG` | Input alternative | ICRS decimal-degree coordinates |
| `--extract` | off | Enable pixel extraction and analysis |
| `--sectors N [N ...]` | all covered | Sectors to attempt |
| `--aperture {circle,mask,auto}` | circle | Aperture selection |
| `--radius PIXELS` | 1.5 | Circular aperture radius, not a sky-match radius |
| `--center X Y` | target position | Zero-based TPF coordinates for circular mask |
| `--mask PATH` | none | Weighted 2-D `.npy` mask |
| `--height`, `--width` | 15, 15 | Odd target-stamp dimensions in pixels |
| `--cutout-size` | 31 | Odd TessCut size containing stamp/background |
| `--background-size` | 31 | Odd upstream background-box size |
| `--aperture-mode` | normal | Upstream initial automatic aperture mode |
| `--correction {standard,pca,none}` | standard | Selected photometry branch |
| `--pca-modes` | 3 | PCA correction component count |
| `--keep-flagged` | off | Retain nonzero quality flags |
| `--sigma VALUE` | off | One-pass median/MAD clipping |
| `--fmin`, `--fmax` | sampling-based | Frequency bounds in microhertz |
| `--oversample` | 5 | Frequency-grid sampling factor |
| `--max-bins` | 1000000 | Grid-size limit |
| `--super-nyquist` | off | Allow above reference Nyquist |
| `--top-peaks` | 10 | Maximum listed local candidate maxima |
| `--output DIR` | results | Output parent directory |
| `--help`, `--version` | — | Usage and version |

## Troubleshooting

- **No coverage returned:** verify coordinates/epoch and inspect the manifest. A failed query must be retried; it is not a negative coverage result.
- **Coverage found but extraction failed:** inspect eleanor/TessCut availability, upstream dependency compatibility, catalog metadata, recent-sector support and service status. Do not relabel the sector absent.
- **Aperture outside stamp:** enlarge the target stamp and containing cutout or choose a smaller, physically justified mask.
- **Unexpected variability:** compare raw/standard/PCA outputs, inspect background/crowding and neighboring sources, change aperture deliberately, and assess aliases.
- **No expected rapid pulsation:** check cadence, exposure attenuation, quality and signal-to-noise; consider USC/SC observations.
- **Large grid:** narrow the interval; do not assume more bins create more resolving power.
- **Several targets:** this initial CLI processes one target per command. Run separate commands/output directories; batch-catalog orchestration is not implemented.

On a headless Linux server:

```bash
MPLBACKEND=Agg ffi-tess --tic 422526868 --extract --output results
```

## Reproducibility and validation

Record the command, source commit/release, target coordinates, masks, manifests, cache, and versions:

```bash
python --version
ffi-tess --version
python -m pip freeze > requirements-used.txt
```

Run tests:

```bash
python -m pip install -e ".[dev]"
MPLBACKEND=Agg python -m pytest -q
```

The generation environment passed **29 tests**, including mocked coverage and eleanor-adapter contracts. One Astropy spectrum-integration module was skipped. Mocked calls do not establish compatibility with real eleanor or MAST. The skipped test uses an explicitly analytical sine-wave fixture, not observed data or a scientific result.

GitHub Actions installs the base runtime and runs offline tests; it does **not** perform a live extraction or install eleanor. Follow [VALIDATION.md](VALIDATION.md) to test those separately, including real examples from each available FFI cadence and signal-preservation checks before calling a release stable.

## Credits and licensing

Original wrapper code: copyright (c) 2026 Murat Uzundag, under the [MIT License](LICENSE). eleanor is separately installed, MIT licensed, and remains the work of its authors. See [THIRD_PARTY.md](THIRD_PARTY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

If eleanor contributes to a publication, follow its guidance to cite Feinstein et al. (2019). This wrapper forces TessCut mode, so follow the TessCut citation guidance for Brasseur et al. (2019), plus applicable tess-point, TESS/SPOC, MAST and scientific-library acknowledgments. See the [eleanor repository](https://github.com/afeinstein20/eleanor) and [documentation](https://adina.feinste.in/eleanor/).

[CITATION.cff](CITATION.cff) supplies local software metadata; cite a specific archived version if one is later assigned a DOI. No existing DOI is claimed.

The [banner and emblem](assets/README.md) are decorative pixel/aperture artwork, not actual observations or official mission logos. For initial publication instructions, see [UPLOAD_TO_GITHUB.md](UPLOAD_TO_GITHUB.md).
