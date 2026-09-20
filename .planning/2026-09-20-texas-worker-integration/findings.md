# Findings

- Fort Worth has local commit `4042f13`: fixed the null address collapse that reduced hundreds of rows to one lead.
- San Antonio/San Marcos has local commit `aad6506`: improved San Antonio from 2 to 29 kept leads and San Marcos from 4 to 8.
- Houston has local commit `e800cd3`: kept Houston city permits enabled, removed three false-positive non-leads, and passed checks.
- Healthy-source proof has local commit `8628506`: found no Dallas-style under-read across Tarrant, Arlington, TABS, and TDHCA, but documented caveats.
- Buyer-facing counts has local commit `8e14e31`: fixed public counts, labels, Dallas cleanup, and summary fields, with checks passing in its worker.
