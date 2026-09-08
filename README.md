# LLE Patch Report Solution

This directory contains a self-contained report generator for LLE patch reporting.

## What it does

- Reads the Ansible inventory definitions from `/git_incomm/incomm_git_inventory`, including the LWR and PROD inventory files.
- Reads the already-copied host data files from /inventory, which contain the patching details collected from each server.
- Matches inventory hosts to `/inventory` files by hostname prefix: it checks the exact filename first, then the hostname before the first dot. For example, `host.example.com` matches either `/inventory/host.example.com` or `/inventory/host`.
- Removes duplicate Ansible entries that have the same hostname prefix, even when they appear in multiple inventory files.
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

Run the report using the Ansible inventories from `/git_incomm/incomm_git_inventory` and compare each host against its copied data file in `/inventory` for LLE (default):

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

- The generator reads Ansible inventory files only from `/git_incomm/incomm_git_inventory`.
- The copied host files in `/inventory` remain the comparison source for patching details.
- Hosts present in Ansible inventory but missing from `/inventory` are listed in the issues table for review, such as possible decommissioned machines.
- It does not modify scripts or files outside this directory.
- The HTML report is intended for management presentation and can be shared as-is.
