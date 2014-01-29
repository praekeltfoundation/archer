import datetime
import uuid

class ValidationError(Exception):
    """Validation failed"""


class UnknownFieldError(ValidationError):
    """Field not in schema"""


def validate_timestamp(value):
    try:
        datetime.datetime.utcfromtimestamp(value / 1000.0)
    except ValueError:
        raise ValidationError('%s is not a valid timestamp' % value)


def validate_uuid(value):
    try:
        uuid.UUID(value)
    except TypeError:
        raise ValidationError('%s is not a valid UUID' % value)


class Schema(object):
    def __init__(self, schema):
        self.schema = schema

    def _isrequired(self, k):
        return self.schema[k].get('required', True)

    def validate(self, content):
        for k, v in self.schema.items():
            if (not k in content) and self._isrequired(k):
                raise ValidationError("Key '%s' must exist in schema" % k)

        for k, v in content.items():
            if not k in self.schema:
                raise ValidationError("Key '%s' does not exist in schema" % k)
 
            if self._isrequired(k) and (v is None):
                raise ValidationError("Key '%s' must not be None" % k)

            if v is not None:
                type = self.schema[k]['type']
                if not isinstance(v, type):
                    raise ValidationError("'%s': %s, is not type %s" % (
                        k, repr(v), type
                    ))

                for validator in self.schema[k].get('validators', []):
                    validator(v)
