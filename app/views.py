import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, Ticket, User
from .models import Event, Comment


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
        {"event": event, "user_is_organizer": request.user.is_organizer},
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
def ticket_list(request):
    # Obtener solo los tickets del usuario logueado
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'app/ticket_list.html', {'tickets': tickets})

# View para crear o editar un ticket
@login_required
def ticket_form(request, event_id=None, id=None):
    ticket = None
    event = None
    if id:
        ticket = get_object_or_404(Ticket, pk=id, user=request.user)
        if not ticket.can_be_modified_by_user(request.user):
            return redirect("home")
        event= ticket.event
    elif event_id:
        event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        quantity = request.POST.get("quantity")
        type_ = request.POST.get("type")
        event_id_post = request.POST.get("event_id")

        if ticket:
            ticket.quantity = quantity
            ticket.type = type_
        else:
            event = get_object_or_404(Event, pk=event_id_post)
            ticket = Ticket.objects.create(
                quantity = quantity,
                type=type_,
                user=request.user,
                event=event
            )
        ticket.save()
        return redirect("ticket_list")
    
    return render(request, "app/ticket_form.html", { "ticket": ticket, "event" : event})

# View para ver el detalle de un ticket
@login_required
def ticket_detail(request, id):
    ticket = get_object_or_404(Ticket, pk=id, user=request.user)
    return render(request, "app/ticket_detail.html", {"ticket": ticket})

# View para eliminar tickets
@login_required
def ticket_delete(request, id):
    ticket=get_object_or_404(Ticket, pk=id, user=request.user)

    if request.method=="POST" and ticket.can_be_deleted_by_user(request.user):
        ticket.delete()
        return redirect("ticket_list")
    return render(request, "app/ticket_delete.html", {"ticket": ticket})
    