# urls.py
from django.urls import path
# to import the view above
from . import views

# specific a variable (urlpatterns)
# make it equal to a list
# what it does is to call the views.home function when visting to base url of the website
urlpatterns = [
	# empty path "" = go to the base url of the website
	# connect to views.home
    path("", views.leafletmapajax, name="leafletmap"),
    path('country_search/', views.CountrySearchView.as_view(), name='country_search'),
    path('artist_search/', views.ArtistSearchView.as_view(), name='artist_search'),
    path('collections/', views.collections, name='collections'),
    path('collections/create/', views.create_collection, name='create_collection'),
    path('collections/get_user_collections/', views.get_user_collections, name='get_user_collections'),
    path('add_release/', views.add_release_to_collection, name='add_release_to_collection'),
    path('collection/<str:collection_id>/', views.collection_detail, name='collection_detail'),
    path('delete_collection/<str:collection_id>/', views.delete_collection, name='delete_collection'),
    path('release/<str:release_id>/', views.release_detail, name='release_detail'),
    path('delete_release_from_collection/<str:collection_id>/<str:release_id>/', views.delete_release_from_collection, name='delete_release_from_collection'),
]