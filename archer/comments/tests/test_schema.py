from twisted.trial import unittest
from twisted.internet import defer

from archer.comments.persistence import utils

class SchemaTest(unittest.TestCase):
    def test_validate(self):
        schema = utils.Schema({
            'name': str,
            'phone': int,
            'pencils': list
        })

        good = {
            'name': 'test',
            'phone': 5551023,
            'pencils': ['green', 'red']
        }

        bad = {
            'name': 141231,
            'phone': {},
            'pencils': ['green', 'red']
        }
        schema.validate(good)

        self.assertRaises(utils.ValidationError, schema.validate, bad)
