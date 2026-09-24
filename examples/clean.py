import bizpack as bp

input_file = r"C:\Users\gsudh\.gemini\antigravity\scratch\bizkit\examples\dirty_sales_v2.csv"
output_file = r"C:\Users\gsudh\.gemini\antigravity\scratch\bizkit\examples\clean_sales.csv"

# Cleans mixed dates, converts currencies to INR, and saves clean_sales.csv
bp.clean_file(input_file, output_file, target_currency="INR")
