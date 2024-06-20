from django.urls import path
# to import the view above
from . import views

# specific a variable (urlpatterns)
# make it equal to a list
# what it does is to call the views.home function when visting to base url of the website
urlpatterns = [
	# empty path "" = go to the base url of the website
	# connect to views.home
	path("", views.home, name="home"),
    path("todos/", views.todos, name="todos"),
    path("leafletmap/", views.leafletmap, name="leafletmap")
]