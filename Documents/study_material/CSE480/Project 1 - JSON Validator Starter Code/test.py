import unittest

class TestCase(unittest.TestCase):
    def test_1(self):
        from Project1.project import NotWellFormedError, 
            NotValidError, build_validator

        int_validator = build_validator("""{"type": "integer"}""")
        int_validator.validate("5")        

        with self.assertRaises(NotWellFormedError):
            int_validator.validate("josh") 
        with self.assertRaises(NotValidError):
            int_validator.validate("null") 
        with self.assertRaises(NotValidError):
            int_validator.validate("4.0") 

if __name__ == "__main__":
    unittest.main()
