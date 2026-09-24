import bizpack as bp
print("Before cleaning:\n", bp.read_csv("dirty_data.csv", clean=False).head(10))
clean_df = bp.clean_file("dirty_data.csv", "clean_data.csv", target_currency="INR")
print("\nAfter cleaning:\n", clean_df.head(10))
