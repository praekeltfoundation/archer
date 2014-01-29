import uuid

from twisted.internet import defer
from riakasaurus import riak
from archer.comments.persistence import utils


class Comment(object):
    def __init__(self, client):
        self.client = client

        self.comment_schema = utils.Schema({
            'author':    {'type': str},
            'time':      {'type': int},
            'comment':   {'type': str},
            'parent':    {'type': uuid.UUID, 'required': False},
            'resource':  {'type': uuid.UUID}
        })

    def _get_bucket(self, resource)
        return self.client.bucket('comment_%' % resource)

    @defer.inlineCallbacks
    def add(self, author, time, resource, comment, parent=None):
        """Add a comment"""
        doc = {
            'author': author,
            'time': time,
            'resource': resource,
            'comment': comment,
            'parent': parent
        }

        self.comment_schema.validate(doc)

        comment_id = uuid.uuid4()
        b = self._get_bucket(resource)

        comment = b.new(comment_id, doc)
        comment.add_index('time_int', time)

        yield comment.store()

        defer.returnValue(comment_id)

    def hide(self, commentid):
        pass

