from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from myapp.models import Release, ReleaseList
from django.contrib.auth.models import User
import json

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
    def test_country_search_view_server_error(self, mock_cache_by_release, mock_search_releases):
        # Mock an exception being raised by musicbrainzngs.search_releases
        mock_search_releases.side_effect = Exception('Test Exception')
        
        # Mock the cache_by_release function to return 12 valid URLs
        mock_cache_by_release.return_value = ['http://example.com/image.jpg'] * 12

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

class ReleaseCollectionTests(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')

        # Create a ReleaseList
        self.collection = ReleaseList.objects.create(name='Test Collection', user=self.user)
        self.release = Release.objects.create(release_id='12345', title='Test Release', cover_image='http://example.com/image.jpg')
        self.collection.releases.add(self.release)

    def test_add_release_to_collection(self):
        # Define the release data
        release_data = {
            'id': '12345',
            'title': 'Test Release',
            'cover_image': 'http://example.com/image.jpg',
            'release_data': {'id': '12345', 'title': 'Test Release'}
        }

        # Make a POST request to add the release to the collection
        response = self.client.post(
            reverse('add_release_to_collection'),
            data=json.dumps({
                'collection_id': str(self.collection.id),
                'release': release_data
            }),
            content_type='application/json'
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf-8'), {'success': True})

        # Check that the release was added to the collection
        self.assertTrue(self.collection.releases.filter(release_id='12345').exists())

    def test_add_release_to_collection_invalid_json(self):
        # Make a POST request with invalid JSON
        response = self.client.post(
            reverse('add_release_to_collection'),
            data='invalid json',
            content_type='application/json'
        )

        # Check the response
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content.decode('utf-8'), {'success': False, 'error': 'Invalid JSON'})

    def test_get_user_collections(self):
        # Make a GET request to fetch user collections
        response = self.client.get(reverse('get_user_collections'))

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertIn('collections', response.json())
        self.assertEqual(len(response.json()['collections']), 1)
        self.assertEqual(response.json()['collections'][0]['name'], 'Test Collection')

    def test_create_collection(self):
        # Define the collection data
        collection_data = {
            'name': 'New Collection'
        }

        # Make a POST request to create a new collection
        response = self.client.post(
            reverse('create_collection'),
            data=collection_data,
        )

        # Check the response
        self.assertEqual(response.status_code, 201)
        self.assertJSONEqual(response.content.decode('utf-8'), {'success': True, 'redirect_url': reverse('collections')})

        # Check that the collection was created
        self.assertTrue(ReleaseList.objects.filter(name='New Collection', user=self.user).exists())

    def test_delete_collection(self):
        response = self.client.post(reverse('delete_collection', args=[self.collection.id]))
        self.assertRedirects(response, reverse('collections'))
        self.assertFalse(ReleaseList.objects.filter(id=self.collection.id).exists())

    def test_collection_detail(self):
        response = self.client.get(reverse('collection_detail', args=[self.collection.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'collection_detail.html')
        self.assertContains(response, self.collection.name)

    def test_delete_release_from_collection(self):
        # Make a POST request to delete the release from the collection
        response = self.client.post(reverse('delete_release_from_collection', args=[self.collection.id, self.release.release_id]))

        # Check the response
        self.assertRedirects(response, reverse('collection_detail', args=[self.collection.id]))
        # Check that the release was removed from the collection
        self.assertFalse(self.collection.releases.filter(release_id=self.release.release_id).exists())
        # Check that the release was deleted since it is not part of any other collections
        self.assertFalse(Release.objects.filter(release_id=self.release.release_id).exists())

    def test_delete_release_from_collection_in_other_collections(self):
        # Create another collection and add the same release to it
        another_collection = ReleaseList.objects.create(name='Another Collection', user=self.user)
        another_collection.releases.add(self.release)
        # Make a POST request to delete the release from the first collection
        response = self.client.post(reverse('delete_release_from_collection', args=[self.collection.id, self.release.release_id]))
        # Check the response
        self.assertRedirects(response, reverse('collection_detail', args=[self.collection.id]))
        # Check that the release was removed from the first collection
        self.assertFalse(self.collection.releases.filter(release_id=self.release.release_id).exists())
        # Check that the release still exists since it is part of another collection
        self.assertTrue(Release.objects.filter(release_id=self.release.release_id).exists())

    def test_release_detail_existing_release(self):
        # Make a GET request to the release_detail view for an existing release
        response = self.client.get(reverse('release_detail', args=[self.release.release_id]))

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'release_detail.html')
        self.assertContains(response, self.release.title)
        self.assertContains(response, self.release.cover_image)

    def test_release_detail_non_existing_release(self):
        # Make a GET request to the release_detail view for a non-existing release
        response = self.client.get(reverse('release_detail', args=['non_existing_release_id']))

        # Check the response
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(response.content.decode('utf-8'), {'success': False, 'error': 'Release not found'})

    def test_release_detail_create_release(self):
        # Define the release data
        release_data = {
            'id': '67890',
            'title': 'New Release',
            'cover_image': 'http://example.com/new_image.jpg',
            'release_data': {'id': '67890', 'title': 'New Release'}
        }

        # Make a POST request to create a new release
        response = self.client.post(
            reverse('release_detail', args=['67890']),
            data=json.dumps({'release': release_data}),
            content_type='application/json'
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf-8'), {'success': True, 'release_id': '67890'})

        # Check that the release was created
        self.assertTrue(Release.objects.filter(release_id='67890').exists())

    def test_release_detail_invalid_json(self):
        # Make a POST request with invalid JSON
        response = self.client.post(
            reverse('release_detail', args=['67890']),
            data='invalid json',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content.decode('utf-8'), {'success': False, 'error': 'Invalid JSON'})
