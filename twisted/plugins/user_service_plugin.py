from twisted.application.service import ServiceMaker

serviceMaker = ServiceMaker(
    'user-service', 'archer.users.user_service',
    'RESTful service for user management.', 'user-service')
