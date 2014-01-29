from aludel.service import service, handler

@service
class CommentServiceApp(object):

    def __init__(self, reactor=None):
        pass

    @handler('/', methods=['GET'])
    def create_user(self, request):
        return {'content': 'hello world'}
