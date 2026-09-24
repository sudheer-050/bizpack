"""
Generate a realistic, dirty 1,000-record business spreadsheet export.
Includes:
- Messy headers with spaces, slashes, parentheses, and currency symbols
- Accounting negatives: (1,250.00), ($450.00)
- Currencies with commas: $14,250.00, €5,200.50, £1,100
- Percentages: 25.4%, (4.2%), 12.0%
- Protected ID columns with leading zeros: 00104, 07001
- Placeholder nulls: '-', 'N/A', ' — ', '#VALUE!', 'None'
- Mixed boolean styles: Y/N, Yes/No, true/false
- Notes column with occasional dollar signs (tests threshold guardrail)
- Blank rows and trailing 'Grand Total' summary footer
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd

random.seed(42)

COMPANIES = [
    "Acme Corp", "Globex Inc", "Initech LLC", "Umbrella Corp", "Wayne Enterprises",
    "Stark Industries", "Cyberdyne Systems", "Soylent Corp", "Massive Dynamic",
    "Hooli Inc", "Dunder Mifflin", "Vandelay Industries", "Pied Piper", "Wonka Industries"
]

REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
TIERS = ["Bronze", "Silver", "Gold", "Enterprise", "VIP Platinum"]

CURRENCIES = ["$", "$", "$", "€", "£"]  # mostly USD, some EUR and GBP

NULL_PLACEHOLDERS = ["-", "N/A", "—", "None", "", "#VALUE!"]

start_date = datetime(2024, 1, 1)

rows = []

for i in range(1, 1001):
    # Customer and ID
    company = random.choice(COMPANIES)
    # Leading zero IDs (e.g. 00101 to 00999)
    acct_id = f"{random.randint(1, 999):05d}"
    
    # Order Date
    order_date = (start_date + timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
    region = random.choice(REGIONS)
    
    # Revenue (dirty formatting)
    base_rev = round(random.uniform(500, 75000), 2)
    curr = random.choice(CURRENCIES)
    
    # 8% chance of being negative (refund / return / credit memo)
    is_neg = (random.random() < 0.08)
    # 4% chance of being placeholder null
    is_null_rev = (random.random() < 0.04)
    
    if is_null_rev:
        rev_str = random.choice(NULL_PLACEHOLDERS)
    elif is_neg:
        neg_style = random.choice(["paren", "curr_paren", "minus"])
        if neg_style == "paren":
            rev_str = f"({base_rev:,.2f})"
        elif neg_style == "curr_paren":
            rev_str = f"({curr}{base_rev:,.2f})"
        else:
            rev_str = f"-{curr}{base_rev:,.2f}"
    else:
        rev_str = f"{curr}{base_rev:,.2f}" if random.random() < 0.8 else f"{base_rev:,.2f}"
    
    # Margin % (dirty formatting)
    margin_val = round(random.uniform(5.0, 55.0), 1)
    if is_neg:
        margin_str = f"({margin_val:.1f}%)"
    elif random.random() < 0.05:
        margin_str = random.choice(["-", "N/A", ""])
    else:
        margin_str = f"{margin_val:.1f}%"
    
    # Unit Cost
    cost_val = round(base_rev * (1 - (margin_val / 100)), 2)
    cost_str = f"${cost_val:,.2f}" if not is_null_rev else "-"
    
    # Booleans (Active Customer?)
    bool_style = random.choice(["Y", "N", "Yes", "No", "true", "false", "Y", "Yes"])
    
    # Notes column (Real text with occasional numbers to test threshold protection!)
    notes_options = [
        "Standard order",
        "Quarterly renewal",
        "Customer asked for $50 discount",
        "VIP client priority support",
        "Account upgrade pending",
        "Fast shipping requested",
        ""
    ]
    note = random.choice(notes_options)
    
    rows.append({
        " Customer Name / Client ": company,
        " Account # ": acct_id,
        " Order Date (UTC) ": order_date,
        " Region / Territory ": region,
        " Gross Revenue ($) ": rev_str,
        " Unit Cost ($) ": cost_str,
        " Profit Margin % ": margin_str,
        " Active Subscription? ": bool_style,
        " Customer Notes / Log ": note
    })

# Insert a couple of completely blank rows to test drop_empty()
rows.insert(250, {k: "" for k in rows[0].keys()})
rows.insert(750, {k: None for k in rows[0].keys()})

# Append a classic Excel 'Grand Total' summary footer row at the bottom
rows.append({
    " Customer Name / Client ": "Grand Total",
    " Account # ": "N/A",
    " Order Date (UTC) ": "-",
    " Region / Territory ": "Summary",
    " Gross Revenue ($) ": "$28,452,100.80",
    " Unit Cost ($) ": "$17,210,400.00",
    " Profit Margin % ": "39.5%",
    " Active Subscription? ": "",
    " Customer Notes / Log ": "Auto-generated report total"
})

df = pd.DataFrame(rows)

# Add an entirely blank column to test column dropping
df[" Blank Column (Notes) "] = ""

output_path = os.path.join(os.path.dirname(__file__), "dirty_sales_1k.csv")
df.to_csv(output_path, index=False)
print(f"Generated {len(df)} rows to {output_path}")
print("Columns:", list(df.columns))
