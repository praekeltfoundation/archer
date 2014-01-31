import json
from uuid import uuid4

from mock import patch

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.conf import settings

from app.api import register, InvalidResponse, authenticate


class RequestsResponse:
    def __init__(self, status_code=None, response=None):
        self.status_code = status_code
        self.text = response


class ApiTestCase(TestCase):

    def setUp(self):
        self.user = {
            'username': 'joesoap',
            'password': '1234',
            'email': 'some@email.com',
            'msisdn': '27123456789',
        }

    @patch('requests.put')
    def test_registration_success(self, mock_put):
        mock_put.return_value = RequestsResponse(200)
        response = register(self.user)
        self.assertEquals(response.status_code, 200)
        mock_put.assert_called_with(
            settings.USER_SERVICE_URL, json.dumps(self.user))

    @patch('requests.put')
    def test_registration_fail(self, mock_put):
        mock_put.return_value = RequestsResponse(400)
        with self.assertRaises(InvalidResponse):
            register(self.user)
        mock_put.assert_called_with(
            settings.USER_SERVICE_URL, json.dumps(self.user))

    @patch('requests.post')
    def test_authentication_success(self, mock_post):
        uuid = uuid4()
        mock_post.return_value = RequestsResponse(200, json.dumps({
            'user_id': uuid.hex,
        }))

        response = authenticate('joesoap', '1234')
        self.assertEquals(response, json.dumps({
            'user_id': uuid.hex
        }))
        mock_post.assert_called_with(
            settings.USER_SERVICE_URL, json.dumps({
                'username': 'joesoap',
                'password': '1234',
            }))

    @patch('requests.post')
    def test_authentication_fail(self, mock_post):
        mock_post.return_value = RequestsResponse(400)

        with self.assertRaises(InvalidResponse):
            authenticate('joesoap', 'invalid password')
        mock_post.assert_called_with(
            settings.USER_SERVICE_URL, json.dumps({
                'username': 'joesoap',
                'password': 'invalid password'
            }))

    @patch('requests.post')
    @patch('requests.put')
    def test_registration_view(self, mock_put, mock_post):
        put_response = RequestsResponse()
        put_response.status_code = 200
        mock_put.return_value = put_response

        post_response = RequestsResponse()
        post_response.status_code = 200
        post_response.text = 'random-uuid-for-the-user'
        mock_post.return_value = post_response

        client = Client()

        resp = client.get('/')
        self.assertNotContains(resp, 'Logout')

        resp = client.get('/join/')
        self.assertContains(resp, 'Enter the same password as above')

        data = {
            'username': 'joesoap',
            'password1': '1234',
            'password2': '1234',
            'email': 'test@email.com',
            'mobile_number': '27123456789',
        }
        resp = client.post('/join/', data)
        self.assertEquals(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='joesoap').exists())

        resp = client.get('/')
        self.assertContains(resp, 'Logout')

        #test api error result
        put_response.status_code = 400
        mock_put.return_value = put_response
        resp = client.post('/join/', data)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'A user with that username already exists.')

        #test auth error after register
        put_response.status_code = 200
        mock_put.return_value = put_response
        post_response.status_code = 400
        mock_post.return_value = post_response

        resp = client.post('/join/', data)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'Error. Please try again later')

        #Logout and test Login view
        client.get('/logout/')

        resp = client.get('/')
        self.assertNotContains(resp, 'Logout')

        post_response.status_code = 200
        mock_post.return_value = post_response

        data = {
            'username': 'joesoap',
            'password': '1234'
        }
        resp = client.post('/login/', data)
        self.assertEquals(resp.status_code, 302)

        resp = client.get('/')
        self.assertContains(resp, 'Logout')
