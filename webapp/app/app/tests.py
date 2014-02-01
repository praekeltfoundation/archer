from mock import patch
from django.test import TestCase
from django.test.client import Client
from app.api import register, InvalidResponse, authenticate
from django.contrib.auth.models import User


class RequestsResponse:
    def __init__(self, status_code=None, response=None):
        self.status_code = status_code
        self.text = response


class ApiTestCase(TestCase):
    @patch('requests.put')
    def test_registration(self, mock_put):
        requests_response = RequestsResponse()
        requests_response.status_code = 200
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
