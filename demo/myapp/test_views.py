from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch

class CountrySearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('country_search') 

    @patch('musicbrainzngs.search_releases')
    @patch('myapp.views.fetch_cover_image_from_release')
    def test_country_search_view_success(self, mock_get_image_urls, mock_search_releases):
        # Mock the response from musicbrainzngs.search_releases
        mock_search_releases.return_value = {
            'release-list': [{'id': '1', 'title': 'Test Release'}],
            'release-count': 1
        }
        
        # Mock the get_image_urls function to return 12 valid URLs
        mock_get_image_urls.return_value = ['http://example.com/image.jpg'] * 12

        response = self.client.get(self.url, {'ISO_A2': 'US', 'selected_release_types': 'album'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('releases', response.json())
        self.assertEqual(len(response.json()['releases']), 12)

    def test_country_search_view_missing_country(self):
        response = self.client.get(self.url, {'selected_release_types': 'album'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Country parameter is missing')

    @patch('musicbrainzngs.search_releases')
    @patch('myapp.views.fetch_cover_image_from_release')
    def test_country_search_view_server_error(self, mock_get_image_urls, mock_search_releases):
        # Mock an exception being raised by musicbrainzngs.search_releases
        mock_search_releases.side_effect = Exception('Test Exception')
        
        # Mock the get_image_urls function to return 12 valid URLs
        mock_get_image_urls.return_value = ['http://example.com/image.jpg'] * 12

        response = self.client.get(self.url, {'ISO_A2': 'US', 'selected_release_types': 'album'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Test Exception')

class ArtistSearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('artist_search') 

    @patch('musicbrainzngs.search_artists')
    def test_artist_search_view_success(self, mock_search_artists):
        # Mock the response from musicbrainzngs.search_artists
        mock_search_artists.return_value = {
            'artist-list': [{'id': '1', 'name': 'Test Artist'}],
            'artist-count': 1
        }

        response = self.client.get(self.url, {'query': 'Test Artist', 'selected_release_types': 'album'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('artist_list', response.json())
        self.assertEqual(len(response.json()['artist_list']), 1)

    def test_artist_search_view_missing_query(self):
        response = self.client.get(self.url, {'selected_release_types': 'album'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'No search term provided')