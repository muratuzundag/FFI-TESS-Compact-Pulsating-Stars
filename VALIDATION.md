# Validation and release checklist

## Checked in the generation environment

- All source/test modules parse successfully.
- 29 tests passed: core validation, apertures, measured sampling, CLI input,
  mocked eleanor custom-aperture correction, mocked availability/error handling.
- An Astropy spectrum integration module was skipped because Astropy is absent.
- Mocked eleanor tests do not import or exercise real eleanor.
- README local links, notebook code syntax, and final archive structure checked.

## Not executed here

- Full clean-environment dependency installation.
- Live TIC lookup, TessCut sector inventory or pixel cutout download.
- Actual eleanor Source/TargetData processing, correction or PCA.
- Real time-convention/header checks, flux-error checks or contamination analysis.
- Offline Astropy single-sinusoid integration test.
- GitHub Actions in the destination repository.
- Broad injection/recovery, alias, false-positive or significance calibration.

## Before a stable release

1. Install base dependencies cleanly, run all offline tests, then install the
   extraction extra in a suitable environment and record versions.
2. Use a verified target to test positive/negative coverage and a deliberate
   service failure. Failure must remain unknown availability, not no coverage.
3. Extract known 1800-s, 600-s and 200-s FFI cases where available; compare sector,
   detector, position, sampling and original FITS timing metadata.
4. Compare raw and corrected custom-aperture results against upstream examples.
   Verify that changing the mask recomputes all relevant photometry/corrections.
5. Inspect crowding, background, centroid motion, saturation, quality flags,
   long gaps and missed samples. Validate high-proper-motion coordinates.
6. Test PCA/no-PCA and aperture choices with independent signal-preservation
   checks. Synthetic injections for validation must be explicitly identified;
   inject at the appropriate pixel/extraction/correction stage to assess the
   complete pipeline, not only the periodogram step.
7. Confirm uncertainty conventions: raw flux_err is not a corrected covariance.
   Test candidate frequency/amplitude recovery and aliases across the search band.
8. Check all requested sectors are attempted and no failed sector is labeled
   extracted. No last-sector result may be called a merged all-sector light curve.
9. Review licensing/coauthor permissions, pin the validated environment, then
   tag/archive the release. Do not invent a DOI or claim upstream endorsement.

Passing tests is not evidence of a universal detection threshold or a verified
astrophysical interpretation. This source snapshot remains a release candidate.
