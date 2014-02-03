User Service
============

.. http:post:: /users/

    Create a new user node.

    :jsonparam string username: The user's username.
    :jsonparam string msisdn: The user's MSISDN.
    :jsonparam string email_address: The user's email address.

    :resheader Content-Type: will always be `application/json`.
    :status 302: and then redirects to :http:get:`/users/(uuid:user_id)/`
    :status 400: when json parameters are invalid or missing.

.. http:put:: /users/(uuid:user_id)/

    Update a user node.

    :jsonparam string username: The user's username.
    :jsonparam string msisdn: The user's MSISDN.
    :jsonparam string email_address: The user's email address.

    :resheader Content-Type: will always be `application/json`.
    :status 200: when update was successful.
    :status 400: when json parameters are invalid or missing.

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
            "username": "the username",
            "msisdn": "27000000000",
            "email_address": "email@domain.com"
        }


.. http:get:: /users/(uuid:user_id)/

    Get a user node.

    :resheader Content-Type: will always be `application/json`.
    :status 200: when the node was found.
    :status 404: when the node was not found.

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
            "username": "the username",
            "msisdn": "27000000000",
            "email_address": "email@domain.com"
        }

.. http:delete:: /users/(uuid:user_id)/

    Delete a user node.

    :status 204: when the node was deleted.
    :status 404: when the node was not found.

    .. sourcecode:: http

        HTTP/1.1 204 No Content
        Vary: Accept

