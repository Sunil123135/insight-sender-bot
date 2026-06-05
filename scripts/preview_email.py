"""
Module: scripts/preview_email.py
Purpose: Render a sample ScrapeSignal email to stdout
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.email.generator (HTML rendering)

Used by:
    - Local email preview
"""

# Local
from src.email.generator import EmailGenerator

if __name__ == "__main__":
    print(EmailGenerator().render_test_email())
