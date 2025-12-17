
import unittest
from PyQt6.QtWidgets import QApplication
import sys
from src.constants import HARD_WHITELIST

# Create app instance for tests if needed
app = QApplication(sys.argv)

class TestConstants(unittest.TestCase):
    def test_whitelist_contains_critical(self):
        self.assertIn("system", HARD_WHITELIST)
        self.assertIn("explorer.exe", HARD_WHITELIST)
        self.assertIn("qt-xkiller.exe", HARD_WHITELIST)

if __name__ == '__main__':
    unittest.main()
