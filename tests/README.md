# Tests

Add focused tests as the corresponding behavior is implemented. Useful candidates include correct parsing of missing-value encodings, preservation of measurement units, and prevention of leakage between training and evaluation partitions.

`test_download.py` covers checksum rejection, repeated offline runs, preservation of modified raw data, and rejection of unexpected archive paths and links. It uses synthetic archives and makes no network requests.

Run `python -m pytest` from the project root after installing the development dependencies, or use the standard library without installing the package:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
