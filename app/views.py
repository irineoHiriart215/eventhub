import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User
from .models import Event, Comment, Category


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    return render(request, "app/event_detail.html", {"event": event})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    categorias = Category.objects.all()

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer, "categorias": categorias},
    )


#Creamos la vista para gestionar los comentarios.
@login_required
def create_comment(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        text = request.POST.get("text")
        
        # Crear el comentario y asociarlo con el evento y el usuario
        comment = Comment.objects.create(
            event=event,
            user=request.user,
            text=text
        )

        # Redirigir de nuevo a la página del evento
        return redirect('event_detail', id=event.id)

    # Si no es POST, redirigir al detalle del evento (por ejemplo, si alguien intenta acceder a esta vista sin enviar datos)
    return redirect('event_detail', id=event.id)

#Vista para editar un comentario
@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if not comment.can_user_delete(request.user):
        return redirect("event_detail", id=comment.event.id)

    if request.method == "POST":
        comment.text = request.POST.get("text")
        comment.save()
        return redirect("event_detail", id=comment.event.id)

    return render(
        request,
        "app/edit_comment.html",
        {"comment": comment, "event": comment.event},
    )
    
#Vista para eliminar un comentario
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if not comment.can_user_delete(request.user):
        return redirect("event_detail", id=comment.event.id)

    if request.method == "POST":
        comment.delete()
        return redirect("event_detail", id=comment.event.id)

    return render(
        request,
        "app/delete_comment.html",
        {"comment": comment, "event": comment.event},
    )
    
# Vista para que el organizador vea todos los comentarios de sus eventos
#@login_required
#def comment_list(request):
#    if not request.user.is_organizer:
#        return redirect("events")
#
#    comments = Comment.objects.filter(event__organizer=request.user).order_by("-created_at")
#    return render(request, "app/comment_list.html", {"comments": comments})

@login_required
def comment_list(request):
    comments = Comment.objects.all()
    return render(request, "app/comment_list.html", {"comments": comments})


@login_required
def create_categoria(request):
    user = request.user
    categoria = {}
    if not user.is_organizer:
        return redirect("categoria")
    
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active")
        categoria = Category.objects.create(
            name = name,
            description = description,
            is_active = is_active )
        return redirect('categoria')

    return render(
        request,
        "app/crearCategoria.html",
        {"categoria": categoria, "user_is_organizer": request.user.is_organizer})


@login_required
def categoria_list(request):
    categorias = Category.objects.all()
    return render(
        request,
        "app/ListaCategoria.html",
        {"categorias": categorias, "user_is_organizer": request.user.is_organizer})
        
@login_required
def edit_categoria(request, category_id):
    categoria = get_object_or_404(Category, pk=category_id)
 
    if not request.user.is_organizer:
        return redirect("categoria")

    if request.method == "POST":
        categoria.name = request.POST.get("name")
        categoria.description = request.POST.get("description")
        categoria.is_active = request.POST.get("is_active")
        categoria.save()
        return redirect('categoria')

    return render(
        request,
        "app/editCategoria.html",
        {"categoria": categoria, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def view_categoria(request, category_id):
    categoria = get_object_or_404(Category, pk=category_id)      
    return render(
        request,
        "app/detailCategoria.html",
        {"categoria": categoria, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def delete_categoria(request, category_id):
    categoria = get_object_or_404(Category, pk=category_id)
    if not request.user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        categoria.delete()
        return redirect("categoria")

    return render(
        request,
        "app/deleteCategoria.html",
        {"categoria": categoria, "user_is_organizer": request.user.is_organizer},
    )