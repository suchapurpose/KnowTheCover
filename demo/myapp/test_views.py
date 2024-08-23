from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from myapp.models import Release, ReleaseList

class CountrySearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('country_search') 

    @patch('musicbrainzngs.search_releases')
    @patch('myapp.views.cache_by_release')
    def test_country_search_view_success(self, mock_cache_by_release, mock_search_releases):
        # Mock the search_releases function
        mock_search_releases.return_value = {
            'release-list': [
                {'id': str(i), 'title': f'Test Release {i}'} for i in range(0, 12)
            ]
        }
        
        # Mock the cache_by_release function
        mock_cache_by_release.side_effect = lambda release_id: f'http://example.com/image_{release_id}.jpg'
        
        client = Client()
        response = client.get(reverse('country_search'), {'ISO_A2': 'US', 'selected_release_type': 'album'})
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('releases', response_data)
        self.assertEqual(len(response_data['releases']), 12)
        for i in range(0, 12):
            self.assertEqual(response_data['releases'][i]['cover_image'], f'http://example.com/image_{i}.jpg')
        self.assertIn('fetch_count', response_data)
        self.assertIn('offset', response_data)

    def test_country_search_view_missing_country(self):
        response = self.client.get(self.url, {'selected_release_types': 'album'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Country parameter is missing')
    
    def test_country_search_view_invalid_country(self):
        response = self.client.get(self.url, {'ISO_A2': 'INVALID', 'selected_release_type': 'album'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Invalid country code')

    @patch('musicbrainzngs.search_releases')
    @patch('myapp.views.cache_by_release')
    def test_country_search_view_server_error(self, mock_get_image_urls, mock_search_releases):
        # Mock an exception being raised by musicbrainzngs.search_releases
        mock_search_releases.side_effect = Exception('Test Exception')
        
        # Mock the get_image_urls function to return 12 valid URLs
        mock_get_image_urls.return_value = ['http://example.com/image.jpg'] * 12

        response = self.client.get(self.url, {'ISO_A2': 'US', 'selected_release_types': 'album'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Test Exception')

class ArtistSearchViewIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('artist_search') 

    @patch('musicbrainzngs.search_artists')
    @patch('musicbrainzngs.search_releases')
    def test_artist_search_view_success(self, mock_search_releases, mock_search_artists):
        # Mock the responses from musicbrainzngs
        mock_search_artists.return_value = {
            'artist-list': [
                {'id': '1', 'name': 'Artist One'},
                {'id': '2', 'name': 'Artist Two'}
            ]
        }
        mock_search_releases.return_value = {
            'release-list': [
                {'id': '1', 'release-group': {'id': '1'}, 'title': 'Release One'},
                {'id': '2', 'release-group': {'id': '2'}, 'title': 'Release Two'}
            ]
        }

        response = self.client.get(self.url, {'query': 'test', 'selected_release_type': 'album', 'page': 1, 'offset': 0})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('artist_list', response.json())
        self.assertEqual(len(response.json()['artist_list']), 2)
        self.assertEqual(response.json()['current_page'], 1)
        self.assertEqual(response.json()['total_items'], 2)

    def test_artist_search_view_missing_query(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "No search term provided"})

