"""
Generator script to build a realistic 1,000-row dirty sales dataset
with multi-currency, mixed Indian & US dates, accounting negatives,
protected ID codes, and messy spreadsheet anomalies.
"""

import random
import csv
import os

random.seed(42)

clients = [
    "Dunder Mifflin", "Umbrella Corp", "Cyberdyne Systems", "Soylent Corp",
    "Pied Piper", "Hooli Inc", "Wayne Enterprises", "Stark Industries",
    "Globex Inc", "Massive Dynamic", "Acme Corp", "Initech LLC"
]

regions = ["APAC", "North America", "EMEA", "LATAM", "India", "USA", "Europe"]

notes_pool = [
    "Standard order",
    "Fast shipping requested",
    "VIP client priority support",
    "Quarterly renewal",
    "Customer asked for 50 discount",
    "Account upgrade pending",
    "",
    "N/A",
    "-",
]

bool_pool = ["Y", "Yes", "true", "N", "No", "false"]


def generate_row(i):
    client = random.choice(clients)
    acct = f"{random.randint(10, 999):05d}"
    region = random.choice(regions)

    # Generate dates with deliberate mixed patterns based on regional context
    day_unambig = random.randint(13, 28)
    month_unambig = random.randint(1, 12)
    day_ambig = random.randint(1, 12)
    month_ambig = random.randint(1, 12)
    year = 2024

    date_type = random.random()
    if region in ("APAC", "India"):
        # Indian / APAC format: DD/MM/YYYY
        if date_type < 0.40:
            sep = random.choice(["/", "-", "."])
            date_str = f"{day_unambig:02d}{sep}{month_unambig:02d}{sep}{year}"
        elif date_type < 0.75:
            # Ambiguous Indian date: 05/09/2024 (Sept 5th)
            sep = random.choice(["/", "-"])
            date_str = f"{day_ambig:02d}{sep}{month_ambig:02d}{sep}{year}"
        elif date_type < 0.90:
            date_str = f"{year}-{month_ambig:02d}-{day_unambig:02d}"
        else:
            months_text = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            date_str = f"{day_unambig}-{months_text[month_unambig-1]}-{year}"

        rev_num = round(random.uniform(5000, 250000), 2)
        cost_num = round(rev_num * random.uniform(0.55, 0.92), 2)
        is_neg = random.random() < 0.08
        curr_type = random.random()
        if curr_type < 0.65:
            rev_str = f"₹{rev_num:,.2f}" if not is_neg else f"(₹{rev_num:,.2f})"
            cost_str = f"₹{cost_num:,.2f}"
        elif curr_type < 0.85:
            rev_str = f"Rs. {rev_num:,.2f}" if not is_neg else f"-(Rs. {rev_num:,.2f})"
            cost_str = f"Rs. {cost_num:,.2f}"
        else:
            rev_str = f"{rev_num:,.2f}" if not is_neg else f"({rev_num:,.2f})"
            cost_str = f"₹{cost_num:,.2f}"

    elif region in ("North America", "USA"):
        # US format: MM/DD/YYYY
        if date_type < 0.40:
            sep = random.choice(["/", "-"])
            date_str = f"{month_unambig:02d}{sep}{day_unambig:02d}{sep}{year}"
        elif date_type < 0.75:
            # Ambiguous US date: 05/09/2024 (May 9th)
            sep = random.choice(["/", "-"])
            date_str = f"{month_ambig:02d}{sep}{day_ambig:02d}{sep}{year}"
        elif date_type < 0.90:
            date_str = f"{year}-{month_ambig:02d}-{day_unambig:02d}"
        else:
            date_str = f"{month_unambig:02d}/{day_unambig:02d}/24"

        rev_num = round(random.uniform(100, 75000), 2)
        cost_num = round(rev_num * random.uniform(0.55, 0.92), 2)
        is_neg = random.random() < 0.08
        if random.random() < 0.85:
            rev_str = f"${rev_num:,.2f}" if not is_neg else f"(${rev_num:,.2f})"
            cost_str = f"${cost_num:,.2f}"
        else:
            rev_str = f"{rev_num:,.2f}" if not is_neg else f"({rev_num:,.2f})"
            cost_str = f"${cost_num:,.2f}"

    elif region in ("EMEA", "Europe"):
        # European / UK format: DD/MM/YYYY
        if date_type < 0.40:
            sep = random.choice(["/", ".", "-"])
            date_str = f"{day_unambig:02d}{sep}{month_unambig:02d}{sep}{year}"
        elif date_type < 0.75:
            sep = random.choice(["/", "."])
            date_str = f"{day_ambig:02d}{sep}{month_ambig:02d}{sep}{year}"
        else:
            date_str = f"{year}-{month_ambig:02d}-{day_unambig:02d}"

        rev_num = round(random.uniform(200, 65000), 2)
        cost_num = round(rev_num * random.uniform(0.55, 0.92), 2)
        is_neg = random.random() < 0.08
        if random.random() < 0.55:
            rev_str = f"€{rev_num:,.2f}" if not is_neg else f"(€{rev_num:,.2f})"
            cost_str = f"€{cost_num:,.2f}"
        else:
            rev_str = f"£{rev_num:,.2f}" if not is_neg else f"(£{rev_num:,.2f})"
            cost_str = f"£{cost_num:,.2f}"

    else:  # LATAM
        date_str = f"{day_unambig:02d}/{month_unambig:02d}/{year}"
        rev_num = round(random.uniform(500, 45000), 2)
        cost_num = round(rev_num * random.uniform(0.55, 0.90), 2)
        is_neg = random.random() < 0.08
        rev_str = f"${rev_num:,.2f}" if not is_neg else f"(${rev_num:,.2f})"
        cost_str = f"${cost_num:,.2f}"

    margin_val = round(random.uniform(5.0, 52.0), 1)
    if is_neg:
        margin_str = f"({margin_val}%)"
    elif random.random() < 0.04:
        margin_str = random.choice(["-", "N/A"])
    else:
        margin_str = f"{margin_val}%"

    sub = random.choice(bool_pool)
    note = random.choice(notes_pool)
    blank_col = ""

    return [client, acct, date_str, region, rev_str, cost_str, margin_str, sub, note, blank_col]


def main():
    rows = [generate_row(i) for i in range(1000)]
    headers = [
        " Customer Name / Client ",
        " Account # ",
        " Order Date (UTC) ",
        " Region / Territory ",
        " Gross Revenue ($) ",
        " Unit Cost ($) ",
        " Profit Margin % ",
        " Active Subscription? ",
        " Customer Notes / Log ",
        " Blank Column (Notes) ",
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(base_dir, "dirty_sales_v2.csv")

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)
        # Footer summary row
        writer.writerow([
            "Grand Total",
            "N/A",
            "-",
            "Summary",
            "$28,452,100.80",
            "$17,210,400.00",
            "39.5%",
            "",
            "Auto-generated report total",
            "",
        ])

    print("SUCCESS: Generated 1,000 rows into:", out_path)


if __name__ == "__main__":
    main()
