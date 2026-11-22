"""Reproduce comparisons of military burden across selected Middle Eastern states."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


COUNTRIES = {
    "BHR": "Bahrain", "EGY": "Egypt", "IRN": "Iran", "IRQ": "Iraq",
    "ISR": "Israel", "JOR": "Jordan", "KWT": "Kuwait", "LBN": "Lebanon",
    "OMN": "Oman", "SAU": "Saudi Arabia", "SYR": "Syria", "TUR": "Türkiye",
}
YEARS = list(range(2010, 2025))
INDICATOR = "MS.MIL.XPND.GD.ZS"


def load_panel(root):
    """Validate the frozen API response, retaining nulls as missing observations."""
    provenance = json.loads((root / "data-source.json").read_text())
    raw = (root / "world-bank-snapshot.json").read_bytes()
    if (hashlib.sha256(raw).hexdigest() != provenance["sha256"]
            or len(raw) != provenance["bytes"]):
        raise ValueError("The source snapshot differs from its recorded checksum.")
    metadata, records = json.loads(raw)
    if metadata["pages"] != 1 or metadata["total"] != len(records):
        raise ValueError("The response is not a complete single-page extraction.")
    if any(row["indicator"]["id"] != INDICATOR for row in records):
        raise ValueError("The response contains a different indicator.")
    panel = pd.DataFrame(
        {"iso3": row["countryiso3code"], "year": int(row["date"]),
         "burden_pct_gdp": row["value"]}
        for row in records
    )
    expected = pd.MultiIndex.from_product([COUNTRIES, YEARS], names=["iso3", "year"])
    actual = pd.MultiIndex.from_frame(panel[["iso3", "year"]])
    if actual.has_duplicates or set(actual) != set(expected):
        raise ValueError("Unexpected or duplicate country-year records.")
    panel["burden_pct_gdp"] = pd.to_numeric(panel["burden_pct_gdp"], errors="raise")
    observed = panel["burden_pct_gdp"].dropna()
    if not np.isfinite(observed).all() or observed.lt(0).any():
        raise ValueError("The source includes invalid military-burden values.")
    panel["country"] = panel["iso3"].map(COUNTRIES)
    panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)
    wide = panel.pivot(index="iso3", columns="year", values="burden_pct_gdp")
    complete_codes = wide.index[wide.notna().all(axis=1)].tolist()
    if len(complete_codes) < 3:
        raise ValueError("Insufficient complete countries for the sensitivity analysis.")
    panel["complete_series"] = panel["iso3"].isin(complete_codes)
    return panel, wide, complete_codes


def build_outputs(panel, wide, complete_codes):
    """Use a fixed set of complete country series for comparable annual summaries."""
    balanced = wide.loc[complete_codes]
    summaries = pd.DataFrame(
        {
            "year": YEARS,
            "available_country_count": wide.notna().sum().values,
            "available_case_mean": wide.mean().values,
            "balanced_country_count": len(complete_codes),
            "balanced_mean": balanced.mean().values,
            "balanced_median": balanced.median().values,
        }
    )
    coverage = panel.groupby(["iso3", "country"], as_index=False).agg(
        observed_years=("burden_pct_gdp", "count"),
        complete_series=("complete_series", "first"),
    )
    coverage["missing_years"] = len(YEARS) - coverage["observed_years"]
    coverage["missing_year_list"] = coverage["iso3"].map(
        lambda code: ";".join(str(year) for year in YEARS if pd.isna(wide.loc[code, year]))
    )
    changes = pd.DataFrame(
        {
            "iso3": complete_codes,
            "country": [COUNTRIES[code] for code in complete_codes],
            "burden_2010": balanced[2010].values,
            "burden_2023": balanced[2023].values,
            "burden_2024": balanced[2024].values,
            "change_2010_2024_pp": (balanced[2024] - balanced[2010]).values,
            "change_2023_2024_pp": (balanced[2024] - balanced[2023]).values,
        }
    )
    changes["relative_change_2010_2024_pct"] = 100 * (
        changes["burden_2024"] / changes["burden_2010"] - 1
    )
    omissions = []
    for code in complete_codes:
        remaining = balanced.drop(index=code)
        omissions.append(
            {
                "omitted_iso3": code,
                "omitted_country": COUNTRIES[code],
                "remaining_countries": len(remaining),
                "change_2010_2024_pp": float((remaining[2024] - remaining[2010]).mean()),
                "change_2023_2024_pp": float((remaining[2024] - remaining[2023]).mean()),
            }
        )
    results = {
        "requested_countries": len(COUNTRIES),
        "country_year_records": len(panel),
        "observed_values": int(panel["burden_pct_gdp"].count()),
        "missing_values": int(panel["burden_pct_gdp"].isna().sum()),
        "balanced_country_codes": complete_codes,
        "mean_change_2010_2024_pp": float((balanced[2024] - balanced[2010]).mean()),
        "mean_change_2023_2024_pp": float((balanced[2024] - balanced[2023]).mean()),
        "change_in_cross_country_median_2023_2024_pp": float(balanced[2024].median() - balanced[2023].median()),
        "median_country_change_2023_2024_pp": float((balanced[2024] - balanced[2023]).median()),
        "countries_increasing_2010_2024": int((balanced[2024] > balanced[2010]).sum()),
        "countries_increasing_2023_2024": int((balanced[2024] > balanced[2023]).sum()),
    }
    return summaries, coverage, changes, pd.DataFrame(omissions), results


def draw_figures(annual, changes, omissions, output):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.facecolor": "#faf8f3", "figure.facecolor": "#faf8f3",
        "savefig.facecolor": "#faf8f3",
    })
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.1))
    axes[0].plot(annual["year"], annual["balanced_mean"], color="#214b68", linewidth=2.4, label="Mean, fixed sample")
    axes[0].plot(annual["year"], annual["balanced_median"], color="#ad603e", linewidth=2.4, label="Median, fixed sample")
    axes[0].set_ylabel("Military expenditure (% of GDP)")
    axes[0].set_title("Eleven complete country series", loc="left", fontweight="bold")
    axes[0].set_xticks([2010, 2015, 2020, 2024])
    axes[0].set_ylim(bottom=0)
    axes[0].legend(frameon=False, fontsize=9)
    ordered = changes.sort_values("change_2023_2024_pp")
    colors = ["#214b68" if x >= 0 else "#ad603e" for x in ordered["change_2023_2024_pp"]]
    bars = axes[1].barh(ordered["country"], ordered["change_2023_2024_pp"], color=colors)
    axes[1].bar_label(bars, labels=[f"{v:+.2f}" for v in ordered["change_2023_2024_pp"]], padding=4, fontsize=8)
    axes[1].axvline(0, color="#655d55", linewidth=0.8)
    axes[1].set_xlim(-1.0, 4.0)
    axes[1].set_title("Country changes, 2023–2024", loc="left", fontweight="bold")
    axes[1].set_xlabel("Percentage points of GDP")
    for ax in axes:
        ax.grid(axis="x", alpha=0.15)
        ax.set_axisbelow(True)
    fig.suptitle("One average can hide different trajectories", x=0.03, ha="left", fontsize=17)
    fig.text(0.03, 0.018, "Selected countries. Source: SIPRI Military Expenditure Database, distributed by World Bank WDI.", fontsize=9)
    fig.tight_layout(rect=[0, 0.06, 1, 0.92])
    fig.savefig(output / "military-burden-trends.png", dpi=180)
    plt.close(fig)

    ordered = omissions.sort_values("change_2023_2024_pp")
    full_change = changes["change_2023_2024_pp"].mean()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    bars = ax.barh(ordered["omitted_country"], ordered["change_2023_2024_pp"], color="#214b68")
    ax.bar_label(bars, labels=[f"{v:+.3f}" for v in ordered["change_2023_2024_pp"]], padding=5, fontsize=9)
    ax.axvline(full_change, color="#ad603e", linestyle="--", linewidth=1.8, label=f"All 11 countries: {full_change:+.3f}")
    ax.set_ylabel("Country omitted")
    ax.set_xlabel("Mean change in military expenditure/GDP, 2023–2024 (percentage points)")
    ax.set_xlim(0, max(ordered["change_2023_2024_pp"].max(), full_change) * 1.25)
    ax.set_title("How much does each country affect the average?", loc="left", fontsize=16, pad=18)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="x", alpha=0.15)
    ax.set_axisbelow(True)
    fig.text(0.03, 0.015, "Each bar uses the remaining ten complete countries. Source: SIPRI via World Bank WDI.", fontsize=9)
    fig.tight_layout(rect=[0, 0.055, 1, 1])
    fig.savefig(output / "leave-one-country-out.png", dpi=180)
    plt.close(fig)


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=root)
    parser.add_argument("--output-dir", type=Path, default=root)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    panel, wide, complete = load_panel(args.input_dir)
    annual, coverage, changes, omissions, results = build_outputs(panel, wide, complete)
    for filename, table in [
        ("country-year-panel.csv", panel), ("data-coverage.csv", coverage),
        ("annual-summary.csv", annual), ("country-changes.csv", changes),
        ("leave-one-country-out.csv", omissions),
    ]:
        table.to_csv(args.output_dir / filename, index=False, float_format="%.10f", na_rep="")
    (args.output_dir / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    draw_figures(annual, changes, omissions, args.output_dir)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
