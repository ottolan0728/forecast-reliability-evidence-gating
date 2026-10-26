# End-to-end reconstruction smoke

PASS using separately supplied exact original raw inputs (13 SHA-256 checks), 136 frozen entities, all frozen preprocessing and feature rules, restored model outputs and masks, and 44648 accepted metric/AP checks across 736 configurations. No model fits, inference, calibration refits, optimization or entity changes. Source restoration separately matches all 1433 original files / 14879 column checks with max absolute difference zero. Rejected changed-source fixture is recorded in RECONSTRUCTION_SMOKE_REPORT.json.

The command sequence is documented in REPRODUCE.md. This local pass does not resolve the blocked public availability of four historical CKW files. Newly downloaded changed files were used only for identity checks. All raw/reconstructed observations stay outside the public repository.
