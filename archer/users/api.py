# -*- test-case-name: archer.users.tests.test_api -*-

from aludel.service import service, handler


@service
class UserServiceApp(object):

    def __init__(self, conn_str, reactor):
        pass

    @handler('/', methods=['PUT'])
    def create_user(self, request):
        return {'content': 'hello world'}
