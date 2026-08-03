import unittest
import sys
import os

# Ajustar path para importar o motor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from motor_v2 import minificar_codigo_para_ia

class TestMinifierSpec(unittest.TestCase):
    def test_comment_stripping(self):
        code = "/* comment */\n// line comment\npublic class A {}"
        minified = minificar_codigo_para_ia(code)
        self.assertNotIn("/*", minified)
        self.assertNotIn("//", minified)
        self.assertIn("class A{}", minified)

if __name__ == '__main__':
    unittest.main()
