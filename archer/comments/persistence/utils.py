class ValidationError(Exception):
    """Validation failed"""

class UnknownFieldError(ValidationError):
    """Field not in schema"""

class Schema(object):
    def __init__(self, schema):
        self.schema = schema

    def validate(self, content):
        for k, v in content.items():
            if not k in self.schema:
                raise ValidationError("Key '%s' does not exist in schema" % k)

            if not isinstance(v, self.schema[k]):
                raise ValidationError("'%s': %s, is not type %s" % (
                    k, repr(v), self.schema[k]
                ))
