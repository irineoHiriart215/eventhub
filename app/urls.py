from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path('events/<int:event_id>/comments/', views.create_comment, name='create_comment'),
    path("comments/<int:comment_id>/edit/", views.edit_comment, name="edit_comment"),
    path("comments/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    path("comments/list/", views.comment_list, name="comment_list"),
    #rutas para las categorias
    path('categorias/', views.categoria_list, name="categoria"),
    path('categorias/detalle/<int:category_id>/', views.view_categoria, name="detail_categoria"),    
    path('categorias/create/', views.create_categoria, name="create_categoria"),
    path('categorias/edit/<int:category_id>/', views.edit_categoria, name="edit_categoria"),
    path('categorias/delete/<int:category_id>/', views.delete_categoria, name="delete_categoria"),
    #rutas para los rating
    path("events/<int:event_id>/ratings/", views.rating_list_event, name="rating_list_event"),
    path("events/<int:event_id>/ratings/create/", views.create_rating, name="create_rating"),
    path("ratings/<int:rating_id>/edit/", views.edit_rating, name="edit_rating"),
    path("ratings/<int:rating_id>/delete/", views.delete_rating, name="delete_rating"),
    #rutas para venue
    path("venue/create/", views.create_venue, name="create_venue"),
    path("venue/", views.venue_list, name="venue"),
    path("venue/<int:venue_id>/edit/", views.edit_venue , name="edit_venue"),
    path("venue/<int:venue_id>/", views.view_venue, name="detail_venue"),
    path("venue/<int:venue_id>/delete/", views.delete_venue, name="delete_venue"),
    # Rutas para los tickets 
    path("ticket/create/<int:event_id>", views.ticket_form, name="ticket_form"),
    path("ticket/edit/<int:id>/", views.ticket_form, name="ticket_edit"),
    path("ticket/<int:id>/", views.ticket_detail, name="ticket_detail"),
    path("ticket/<int:id>/delete/", views.ticket_delete, name="ticket_delete"),
    path("tickets/", views.ticket_list, name="ticket_list"),

          
]
