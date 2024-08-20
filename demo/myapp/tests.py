from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Release, ReleaseList
import json

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

        # Check the response
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content.decode('utf-8'), {'success': False, 'error': 'Invalid JSON'})
