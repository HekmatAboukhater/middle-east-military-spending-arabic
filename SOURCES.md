# Sources and reproducibility

## Attribution

**Information from the Stockholm International Peace Research Institute (SIPRI) Military Expenditure Database**, distributed through the World Bank's World Development Indicators. Database DOI [10.55163/CQGC9685](https://doi.org/10.55163/CQGC9685).

The indicator is `MS.MIL.XPND.GD.ZS`, military expenditure as a percentage of GDP. The [World Bank indicator page](https://data.worldbank.org/indicator/MS.MIL.XPND.GD.ZS) identifies SIPRI as the source and links its data terms. SIPRI's [sources and methods](https://www.sipri.org/databases/milex/sources-and-methods), [definitions](https://www.sipri.org/databases/milex/definitions) and [frequently asked questions](https://www.sipri.org/databases/milex/frequently-asked-questions) explain construction and interpretation.

The fixed response was retrieved on 21 November 2026 in America/New_York. Its precise UTC retrieval timestamp appears in [data-source.json](data-source.json). The World Bank response identifies its source update as 11 November 2026. The project uses 2010–2024 as its historical window.

## Request and preservation

```text
https://api.worldbank.org/v2/country/BHR;EGY;IRN;IRQ;ISR;JOR;KWT;LBN;OMN;SAU;SYR;TUR/indicator/MS.MIL.XPND.GD.ZS?date=2010:2024&format=json&per_page=20000
```

[world-bank-snapshot.json](world-bank-snapshot.json) preserves the response bytes. [data-source.json](data-source.json) records the exact request, retrieval time, byte count and SHA-256 digest. A default reproduction reads that snapshot. Later provider revisions therefore leave this historical calculation reproducible.

## Country scope and missingness

The requested set is Bahrain, Egypt, Iran, Iraq, Israel, Jordan, Kuwait, Lebanon, Oman, Saudi Arabia, Syria and Türkiye. It contains 180 country-year records. Fourteen values, all for Syria in 2011–2024, are missing. Syria's 2010 value remains in the supplied panel and the available-case mean. Eleven countries have a complete fifteen-year series and enter the balanced-sample results. Missing values are retained, without interpolation or substitution.

The selected set is documented explicitly so readers can evaluate its coverage. The averages refer to that set. A complete Middle East aggregate requires a broader membership definition and the relevant weights.

## Output dictionary

| Output | Contents |
| --- | --- |
| `country-year-panel.csv` | 180 rows. `burden_pct_gdp` stores the original indicator value, and `complete_series` identifies membership in the balanced sample. Missing source values are empty CSV fields. |
| `data-coverage.csv` | Counts of reported and missing years, missing-year lists and complete-series status for each requested country. |
| `annual-summary.csv` | Available-case country count and mean, plus fixed-sample count, mean and median for each year. |
| `country-changes.csv` | Values in 2010, 2023 and 2024 and their differences. `*_pp` indicates percentage points. The relative-change column uses the 2010 value as its denominator. |
| `leave-one-country-out.csv` | Mean changes after each omission, for both intervals. Each calculation uses ten countries. |
| `results.json` | Main sample counts and numerical results. |
| `military-burden-trends.png` | Mean and median time series and country-specific 2023–2024 changes. |
| `leave-one-country-out.png` | Short-run mean changes after omitting each country. The dashed line shows the full fixed sample. |

The mean gives equal weight to countries. The omission results describe sensitivity to membership. Estimating sampling uncertainty would require a separate statistical framework.

## Source notes and reuse

SIPRI's dataset includes national coverage differences and estimates, explained in its original country notes. This World Bank API response does not carry all those annotations. Users making detailed comparisons of national budgets should consult the underlying SIPRI materials.

This repository includes a small, non-commercial research extract containing one indicator for twelve countries over fifteen years. The extract remains subject to [SIPRI's terms and conditions](https://www.sipri.org/about/terms-and-conditions). Its data rights are distinct from the licences for this project's original code and text. Source organisations have not endorsed this analysis or translation.

The English note was written for this project. The Arabic note translates that text. Preparation, translation and code used AI assistance.
