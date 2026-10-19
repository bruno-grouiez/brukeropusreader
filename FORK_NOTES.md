# Fork-specific extensions

## Purpose

This fork extends `brukeropusreader` with support for additional OPUS blocks
found in Bruker EM27/SUN files and selective block decoding for workflows that
require only a subset of the available data.

The original package documentation is preserved in `README.md`.

## 1. EM27/SUN-specific blocks

Tests with EM27/SUN OPUS files recorded in 2025 confirmed that the reader
exposes the following additional blocks:

- `ScSm2`
- `IgSm2`
- `IgSm2 Data Parameter`

These are the dictionary keys exposed by the reader. In particular, the
tested files expose `IgSm2`, not `Ig2`, as the key.

Available blocks depend on the OPUS file and instrument configuration.
Use `read_file()` to inspect the available decoded keys when examining an
unfamiliar file.

## 2. Selective block reading

### `read_file()`: read all supported blocks

Use `read_file()` when all supported blocks are needed or when inspecting
an unfamiliar OPUS file.

```python
from brukeropusreader import read_file

opus_data = read_file("opus_file.0")
print(list(opus_data.keys()))
```

### `read_blocks()`: read selected blocks

Use `read_blocks()` when only specific blocks are required.

```python
from brukeropusreader import read_blocks

opus_data = read_blocks(
    "opus_file.0",
    ["IgSm Data Parameter"],
)

parameters = opus_data.get("IgSm Data Parameter")
```

The `block_names` argument is a list of OPUS block names. The returned
`OpusData` contains only the requested blocks that are available in the file.

For example, an EM27/SUN workflow that only needs the acquisition timestamp
can request `IgSm Data Parameter` instead of decoding every block.

**Important:** `read_blocks()` still reads the entire file into memory and
parses its metadata. Its performance benefit comes from avoiding the decoding
of unrelated blocks; it does not perform partial disk reads.

### Reading an acquisition timestamp

```python
from brukeropusreader import read_blocks
import pandas as pd

opus_data = read_blocks(
    "opus_file.0",
    ["IgSm Data Parameter"],
)

parameters = opus_data.get("IgSm Data Parameter")

if parameters:
    date = parameters["DAT"]
    time = parameters["TIM"].split(" ")[0]
    timestamp = pd.to_datetime(
        f"{date} {time}",
        dayfirst=True,
    )
```

### Reading an EM27/SUN spectral block

```python
from brukeropusreader import read_blocks

opus_data = read_blocks("opus_file.0", ["ScSm2"])
spectrum = opus_data.get("ScSm2")
```

Use the block names exposed by the reader; names must match the keys returned
by the parser.

## 3. Choosing a reading method

| Requirement | Recommended method |
|---|---|
| Inspect all decoded blocks | `read_file()` |
| Process many blocks from one file | `read_file()` when most blocks are needed |
| Extract acquisition metadata only | `read_blocks()` |
| Retrieve one or a few spectra | `read_blocks()` |
| Explore an unfamiliar OPUS file | `read_file()` |

## 4. Performance benchmark

A benchmark was performed in the `DATABASE_MATHYS` environment using 10 OPUS
files recorded in 2025. It compared `read_file()` and `read_blocks()` when
extracting the `IgSm Data Parameter` block.

Each method was measured three times per file. The median execution time was
calculated for each method and file.

| Metric | `read_file()` | `read_blocks()` |
|---|---:|---:|
| Median execution time across the tested files | 14.7 ms | 0.2 ms |

The median acceleration calculated from the individual file measurements was
approximately **63x**, corresponding to a 98.4% reduction in median execution
time.

The timestamps returned by both methods were identical for all 10 files.

These results are specific to the tested files and environment. They are not
a general performance guarantee and do not represent the runtime of an entire
database-processing workflow.

## 5. Validation status and limitations

The following checks have been performed:

- `read_blocks()` successfully returned the requested
  `IgSm Data Parameter` block.
- The extracted date and time were successfully converted to a Pandas
  timestamp.
- Timestamps from `read_file()` and `read_blocks()` matched on all 10
  benchmark files.
- The tested EM27/SUN files exposed `ScSm2`, `IgSm2`, and
  `IgSm2 Data Parameter`.

Equivalence of the spectral array values returned by `read_file()` and
`read_blocks()` for `ScSm2` and `IgSm2` still needs to be verified separately.
