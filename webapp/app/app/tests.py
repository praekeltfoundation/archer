from mock import patch
from django.test import TestCase
from app.api import register, InvalidResponse, authenticate


class RequestsResponse:
    def __init__(self, status_code=None, response=None):
        self.status_code = status_code
        self.text = response


class ApiTestCase(TestCase):
    @patch('requests.put')
    def test_registration(self, mock_put):
        requests_response = RequestsResponse()
        requests_response.status_code = 200
        requests_response.text = '{"uuid": "random-uuid-for-the-user"}'
        mock_put.return_value = requests_response

        user = {
            'username': 'joesoap',
            'password': '1234',
            'email': 'some@email.com',
            'msisdn': '27123456789',
        }
        response = register(user)
        self.assertEquals(response.status_code, 200)

        requests_response.status_code = 400
        mock_put.return_value = requests_response

        with self.assertRaises(InvalidResponse):
            register(user)

    @patch('requests.post')
    def test_authentication(self, mock_post):
        requests_response = RequestsResponse()
        requests_response.status_code = 200
        requests_response.text = 'random-uuid-for-the-user'
        mock_post.return_value = requests_response

        response = authenticate('joesoap', '1234')
        self.assertEquals(response, 'random-uuid-for-the-user')

        requests_response.status_code = 400
        mock_post.return_value = requests_response

        with self.assertRaises(InvalidResponse):
            authenticate('joesoap', 'invalid password')
