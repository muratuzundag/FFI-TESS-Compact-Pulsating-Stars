# Contributing

Open an issue for changes to aperture selection, detrending, sampling assumptions,
significance thresholds, archive handling or time conventions. Include the exact
command, version/commit, manifest and a minimal shareable example.

Install `python -m pip install -e ".[dev]"` and run
`MPLBACKEND=Agg python -m pytest -q`. Tests involving eleanor mocks are not live
compatibility tests. Add signal-preservation and real-data comparisons for any
change claimed to improve compact-star photometry.

Do not commit credentials, FITS caches, private target lists or notebook outputs.
