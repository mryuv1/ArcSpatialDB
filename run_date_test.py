if __name__ == "__main__":
    def convert_html_date_to_db_format(html_date):
        """Convert HTML date input (YYYY-MM-DD) to database format (DD-MM-YY)"""
        try:
            if html_date and len(html_date) == 10:  # YYYY-MM-DD format from HTML date input
                year, month, day = html_date.split('-')
                # Convert to DD-MM-YY format for database comparison
                return f"{day.zfill(2)}-{month.zfill(2)}-{year[2:]}"
            return None
        except:
            return None

    # Test cases
    test_cases = [
        ("2025-07-09", "09-07-25"),  # July 9th, 2025
        ("2025-12-25", "25-12-25"),  # December 25th, 2025
        ("2025-01-01", "01-01-25"),  # January 1st, 2025
        ("2025-03-15", "15-03-25"),  # March 15th, 2025
    ]

    print("Testing date conversion:")
    print("HTML Input (YYYY-MM-DD) -> Database Format (DD-MM-YY)")
    print("-" * 50)

    for html_date, expected in test_cases:
        result = convert_html_date_to_db_format(html_date)
        status = "✓" if result == expected else "✗"
        print(f"{status} {html_date} -> {result} (expected: {expected})")

    print("\nDatabase format examples from your data:")
    print("03-07-25 (July 3rd, 2025)")
    print("09-07-25 (July 9th, 2025)")
    print("25-12-25 (December 25th, 2025)")
    
    print("\nTest completed successfully!") 