"""Check the frozen curve files against the committed source manifest.

A normal run refuses to price if a hash does not match, and it does not
rewrite the manifest. ``--accept-new-source`` is the explicit version update.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

SVENY_GAP_LIMIT_BP = 0.005
SVENY_GAP_TOLERANCE_BP = 1e-4


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text())


def verify_or_accept(data_dir: Path, accept_new_source: bool) -> dict:
    """Return the manifest after the hash gate.

    On mismatch without the flag, raise SystemExit and do not write.
    With the flag, rewrite only the two hash fields, then return the new manifest.
    """
    manifest_path = data_dir / "source_manifest.json"
    manifest = load_manifest(manifest_path)
    frozen_name = manifest["frozen_file"]
    sveny_name = manifest["published_sveny_excerpt"]
    frozen_path = data_dir.parent / frozen_name if not Path(frozen_name).is_absolute() else Path(frozen_name)
    sveny_path = data_dir.parent / sveny_name if not Path(sveny_name).is_absolute() else Path(sveny_name)
    # Manifest paths are relative to the repository root, which is the parent of data/.
    if not frozen_path.is_file():
        frozen_path = data_dir / Path(frozen_name).name
    if not sveny_path.is_file():
        sveny_path = data_dir / Path(sveny_name).name
    frozen_hash = sha256(frozen_path)
    sveny_hash = sha256(sveny_path)
    expected_frozen = manifest["frozen_file_sha256"]
    expected_sveny = manifest["published_sveny_excerpt_sha256"]
    mismatches = []
    if frozen_hash != expected_frozen:
        mismatches.append(f"frozen curve {frozen_name}: manifest {expected_frozen}, file {frozen_hash}")
    if sveny_hash != expected_sveny:
        mismatches.append(f"published SVENY excerpt {sveny_name}: manifest {expected_sveny}, file {sveny_hash}")
    if mismatches and not accept_new_source:
        detail = "\n".join(mismatches)
        raise SystemExit(
            "Source commitment does not match the files on disk.\n"
            f"{detail}\n"
            "Refusing to price. Update the data version explicitly with --accept-new-source "
            "if this replacement is intentional. A normal run does not rewrite the manifest."
        )
    if mismatches and accept_new_source:
        manifest["frozen_file_sha256"] = frozen_hash
        manifest["published_sveny_excerpt_sha256"] = sveny_hash
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    if "beta_units" not in manifest or "tau_units" not in manifest:
        raise SystemExit(
            "Manifest must state beta_units and tau_units separately "
            "(BETA in percent, TAU in years). Refusing to price."
        )
    return manifest


def sveny_gaps_bp(curves: dict, published: dict, zero_percent_fn) -> dict[str, float]:
    gaps = {}
    for day, levels in published.items():
        beta = curves[day]
        worst = 0.0
        for maturity, published_y in levels.items():
            formula = zero_percent_fn(float(maturity), beta)
            gap = abs((formula - published_y) * 100.0)
            if gap > worst:
                worst = gap
        gaps[day] = worst
    return gaps


def max_sveny_gap_bp(curves: dict, published: dict, zero_percent_fn) -> float:
    gaps = sveny_gaps_bp(curves, published, zero_percent_fn)
    return max(gaps.values()) if gaps else 0.0


def assert_sveny_gap(curves: dict, published: dict, zero_percent_fn) -> float:
    """Fail the run if any published zero disagrees by more than 0.005 bp + tolerance."""
    worst = max_sveny_gap_bp(curves, published, zero_percent_fn)
    limit = SVENY_GAP_LIMIT_BP + SVENY_GAP_TOLERANCE_BP
    if worst > limit:
        raise SystemExit(
            f"Published SVENY differs from the Svensson formula by {worst:.6f} bp, "
            f"above {SVENY_GAP_LIMIT_BP} bp plus {SVENY_GAP_TOLERANCE_BP} bp numerical tolerance. "
            "Refusing to price."
        )
    return worst
