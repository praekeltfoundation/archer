import time

from twisted.trial import unittest
from twisted.internet import defer

from archer.comments.persistence import comment
from riakasaurus import riak

class CommentTest(unittest.TestCase):
    @defer.inlineCallbacks
    def test_add_comment(self):
        client = riak.RiakClient(host='127.0.0.1', port=8098)

        c = comment.Comment(client)

        yield c.add('Colin', int(time.time()*1000), '6e6dd8b5-47f9-4b8c-8fc7-939e06d9da12', 'Capetown sucks')


