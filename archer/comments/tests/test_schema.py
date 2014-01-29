from twisted.trial import unittest
from twisted.internet import defer

from archer.comments.persistence import utils

class SchemaTest(unittest.TestCase):
    def test_validate(self):
        schema = utils.Schema({
            'name': {'type': str},
            'phone': {'type': int},
            'pencils': {'type': list},
            'dogs': {'type': list, 'required': False}
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
