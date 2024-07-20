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
	path("home", views.home, name="home"),
    path("todos/", views.todos, name="todos"),
    path("", views.leafletmapajax, name="leafletmap"),
    path("searchWithID/", views.searchWithID, name="searchWithID"),
    path("getArtistByID/", views.getArtistByID, name="getArtistByID"),
    path("search/", views.search, name="search"), # use search_async for async (only load single cover art currently)
    path('artists_in_country/', views.artists_in_country, name="artists_in_country"),
    path('country_search/', views.CountrySearchView.as_view(), name="country_search"),
]