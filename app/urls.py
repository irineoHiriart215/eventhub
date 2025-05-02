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
    #rutas para los comentarios
    path('events/<int:event_id>/comments/', views.create_comment, name='create_comment'),
    path("comments/<int:comment_id>/edit/", views.edit_comment, name="edit_comment"),
    path("comments/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    path("comments/list/", views.comment_list, name="comment_list"),
    # Rutas para los tickets (chekear)
    path("ticket/create/<int:event_id>", views.ticket_form, name="ticket_form"),
    path("ticket/edit/<int:id>/", views.ticket_form, name="ticket_edit"),
    path("ticket/<int:id>/", views.ticket_detail, name="ticket_detail"),
    path("ticket/<int:id>/delete/", views.ticket_delete, name="ticket_delete"),
    path("tickets/", views.ticket_list, name="ticket_list"),

          
]
