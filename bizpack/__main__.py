"""
CLI entry point for BizPack:
Usage:
    python -m bizpack dirty_sales.csv
    python -m bizpack dirty_sales.csv --currency INR
"""

import sys
from pathlib import Path
from bizpack.cleaner import clean_file


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("\nBizPack - Zero-Friction Spreadsheet Cleaner")
        print("Usage:")
        print("  python -m bizpack <file.csv or file.xlsx>")
        print("  python -m bizpack <file.csv> --currency INR")
        print("  python -m bizpack <file.csv> --currency USD\n")
        return

    input_file = sys.argv[1]
    curr = None
    if "--currency" in sys.argv:
        idx = sys.argv.index("--currency")
        if idx + 1 < len(sys.argv):
            curr = sys.argv[idx + 1]

    clean_file(input_file, target_currency=curr)


if __name__ == "__main__":
    main()
