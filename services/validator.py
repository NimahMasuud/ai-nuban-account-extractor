import re


class Validator:

    def find_ten_digit_number_strict(self, line: str):
        """
        Strict mode — no space stripping.
        Used for non-keyword lines to avoid false positives like BVN.
        Only matches exactly 10 consecutive digits with no spaces between them.
        """
        match = re.search(r'(?<![a-zA-Z\d])\d{10}(?![a-zA-Z\d])', line)
        return match.group() if match else None

    def find_ten_digit_number_relaxed(self, line: str):
        """
        Relaxed mode — strips internal OCR spaces/dashes within digit groups.
        Only used when a keyword label like 'Account No' is found on the line.
        This handles real OCR noise like '012 345 6789' → '0123456789'.
        """
        candidates = re.findall(
            r'(?<![a-zA-Z\d])[\d][\d\s\-]*[\d](?![a-zA-Z\d])|(?<![a-zA-Z\d])\d(?![a-zA-Z\d])',
            line
        )
        for candidate in candidates:
            digits_only = re.sub(r'[\s\-]', '', candidate)
            if len(digits_only) == 10 and digits_only.isdigit():
                return digits_only
        return None

    def extract_account_number(self, lines: list) -> str:
        keywords = ['account', 'acct', 'acc no', 'account no',
                    'nuban', 'acct no', 'account number']

        # Step 1: Keyword proximity — relaxed mode (handles OCR noise)
        # Only on lines that contain an account label
        for line in lines:
            if any(kw in line.lower() for kw in keywords):
                result = self.find_ten_digit_number_relaxed(line)
                if result:
                    return result

        # Step 2: Fallback — strict mode (no space stripping)
        # Prevents BVN, dates, and other spaced numbers from being accepted
        for line in lines:
            result = self.find_ten_digit_number_strict(line)
            if result:
                return result

        return "No account number found"