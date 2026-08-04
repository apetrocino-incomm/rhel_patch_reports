# LLE Patch Report Solution

This directory contains a self-contained report generator for LLE patch reporting.

## What it does

- Reads the LLE host inventory definitions from the LWR patching sources.
- Reads the already-copied host data files from /inventory, which contain the patching details collected from each server.
- Builds a professional HTML report with:
  - a clear header
  - a primary patch-status table
  - a secondary issues table for hosts that could not be assessed
- Runs entirely from this working directory and does not change anything outside it.

## Files

- report_generator.py: main generator
- tests/test_report_generator.py: basic verification tests
- output/lle_patch_report_YYYYMMDD.html: generated example report with a date-stamped filename

## Run locally

Run the report from the existing /inventory files for LLE (default):

```bash
cd /home/CALLING/apetrocino.aa/projects/new_patch_reports
python3 report_generator.py --output-dir output --environment LLE
```

Run the CAT3 report separately:

```bash
cd /home/CALLING/apetrocino.aa/projects/new_patch_reports
python3 report_generator.py --output-dir output --environment CAT3
```

Run the FCV/DMZ report separately:

```bash
cd /home/CALLING/apetrocino.aa/projects/new_patch_reports
python3 report_generator.py --output-dir output --environment FCV_DMZ
```

You can also limit the number of hosts for a quick smoke test:

```bash
cd /home/CALLING/apetrocino.aa/projects/new_patch_reports
python3 report_generator.py --output-dir output --environment LLE --max-hosts 5
```

## Notes

- The generator reads the existing copied host files from /inventory and writes the report inside this working directory.
- It does not modify scripts or files outside this directory.
- The HTML report is intended for management presentation and can be shared as-is.
