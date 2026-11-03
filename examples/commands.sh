#!/usr/bin/env bash
# Usage examples; confirm target identity and archive coverage first.
ffi-tess --tic 422526868 --output results_inventory
ffi-tess --tic 422526868 --extract --output results_extraction
# Replace sectors/coordinates as appropriate. See README before PCA or super-Nyquist use.
