# Data provenance

Dataset source supplied by the assignment:

https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html

Download and extract the original dataset from the project root:

```bash
python scripts/download_data.py
```

The script uses only Python's standard library. It verifies the archive against the following pinned SHA-256 checksum before saving it:

```text
493b2ec7c2e46e93260040194d86ae35fb8579802c048f94f89539d466b7e6ca
```

Archive URL: https://www.phase-trans.msm.cam.ac.uk/map/data/tar/welddb.tar

The original archive contains `welddb.data`, `welddb.info`, and `welddb.tex`. The script preserves these bytes in `raw/` and writes `raw/manifest.json` containing the source URLs, UTC preparation timestamp, archive checksum, and extracted file sizes and checksums. The timestamp describes when the local dataset was prepared; a cached archive may have been downloaded earlier.

- `raw/`: unchanged source files.
- `processed/`: derived files produced by documented preprocessing.

## Format and loading

The verified archive contains 1,652 data rows, each with 44 whitespace-separated columns and no header. The source documentation defines the column order and measurement units. `N` means that a value was not reported; it must be treated as missing rather than zero. Some columns contain categories or weld identifiers.

From a Python session in the project root, load the raw table with:

```python
import pandas as pd

df = pd.read_csv(
    "data/raw/welddb.data",
    sep=r"\s+",
    header=None,
    na_values=["N"],
)
```

The columns initially have integer names from 0 to 43. Assign meaningful names using `welddb.info` before modeling, and document variable definitions and units. This read preserves the source units and does not impute or normalize values.

The linked source page does not state explicit usage terms; do not assume a redistribution license. Keep source attribution in the report.

## Repeated downloads

When the verified archive is cached, the script needs no network access. Existing extracted files are checked against that archive and missing files are restored. If an existing raw file differs, the script stops without replacing it. Move the conflicting file aside and rerun if restoring the source is intended.

If the remote archive changes, checksum validation fails. Review and document any dataset-version change before updating the pinned checksum.

Record the script or notebook and parameters used to produce each processed dataset. Raw files, the archive, the local manifest, and processed datasets are ignored by Git; the downloader and this documentation are committed.
