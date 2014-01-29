from archer.comments.persistence import comment
from aludel.service import service, handler, get_url_params
from riakasaurus import riak


@service
class CommentServiceApp(object):

    def __init__(self, reactor=None):
        self.client = riak.RiakClient(host='127.0.0.1', port=8098)
        self.comment = comment.Comment(self.client)

    @handler('/comment/v1.0/add', methods=['POST'])
    def create_comment(self, request):
        params = get_url_params(request, (
            'author', 'time', 'comment', 'resource'
        ), optional=('parent',))
        
        return self.comment.add(
            params['author'],
            int(params['time']),
            params['resource'],
            params['comment'],
            parent=params.get('parent', None)
        ).addCallback(lambda _: {'content': 'ok'}
        ).addErrback(lambda _: {'content': 'error'})

