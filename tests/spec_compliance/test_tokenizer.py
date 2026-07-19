import unittest
import sys
import os

# Ajustar path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from motor_v2 import estimar_tokens

class TestTokenizerSpec(unittest.TestCase):
    def test_token_count(self):
        text = "public class A {}"
        tokens = estimar_tokens(text)
        self.assertGreater(tokens, 0)
        
    def test_empty_text(self):
        self.assertEqual(estimar_tokens(""), 0)

if __name__ == '__main__':
    unittest.main()
