class ValidationError(Exception):
    """Validation failed"""

class UnknownFieldError(ValidationError):
    """Field not in schema"""

class Schema(object):
    def __init__(self, schema):
        self.schema = schema

    def _isrequired(self, k):
        return self.schema[k].get('required', True)

    def validate(self, content):
        for k,v in self.schema.items():
            if (not k in content) and self._isrequired(k):
                raise ValidationError("Key '%s' must exist in schema" % k)
            
        for k, v in content.items():
            if not k in self.schema:
                raise ValidationError("Key '%s' does not exist in schema" % k)

            if (v is None) and self._isrequired(k):
                raise ValidationError("Key '%s' must not be None" % k)

            try:
                self.schema[k]['type'](v)
            except:
                raise ValidationError("'%s': %s, is not type %s" % (
                    k, repr(v), self.schema[k]
                ))
        
