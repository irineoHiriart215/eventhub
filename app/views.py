import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum

from .models import Event, User, Ticket
from .models import Comment, Category, Rating, Venue



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
    now = timezone.now()
    events = Event.objects.filter(scheduled_at__gt=now).order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    cuenta_regresiva = None
    now = timezone.now()
    if not request.user.is_organizer:
        if event.scheduled_at > now:
            cuenta_regresiva = event.get_cuenta_regresiva()
        else:
            cuenta_regresiva = "El evento ya ha ocurrido."
    
    return render(
            request, "app/event_detail.html",
            {"event": event, "cuenta_regresiva": cuenta_regresiva}
            )


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")
    
    event = get_object_or_404(Event, pk=id)
    if request.method == "POST":
        event.delete()
        return redirect("events")

    return render(
        request,
        "app/event_delete.html",
        {"evento": event, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_form(request, id = None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    categorias = Category.objects.all()
    venues = Venue.objects.all()

    if id is not None:
        event = get_object_or_404(Event, pk=id)
        if event.no_changes_after_cancelled():
            messages.error(request, "No se puede modificar un evento cancelado.")
            return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        state = request.POST.get("state")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        category_id= request.POST.get("categoria")
        category= get_object_or_404(Category,id=category_id)

        venue_id= request.POST.get("venue")
        venue= get_object_or_404(Venue, id=venue_id)
        
        if id is None:
            Event.new(title, description, scheduled_at, request.user, category, venue, state)
        else:
            event.update(title, description, scheduled_at, request.user, category, venue, state)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer, "categorias": categorias, "venues": venues},
    )


@login_required
def create_comment(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip() 
        text = request.POST.get("text", "").strip()
        
        if title and text:
            comment = Comment.objects.create(
                event=event,
                user=request.user,
                title=title,
                text=text
            )
            return redirect('event_detail', id=event.id)
        else:
            error_message = "Ambos campos son obligatorios."
            return render(
                request,
                "app/create_comment.html",
                {"event": event, "error_message": error_message}
            )

    return render(request, "app/create_comment.html", {"event": event})

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if not comment.can_user_delete(request.user):
        return redirect("event_detail", id=comment.event.id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()

        if title and text:
            comment.title = title
            comment.text = text
            comment.save()
            return redirect("event_detail", id=comment.event.id)
        else:
            error_message = "Ambos campos son obligatorios."
    else:
        error_message = None
    return render(
                request,
               "app/edit_comment.html",
                {"comment": comment, "event": comment.event, "error_message": error_message}
            )
    
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    event = comment.event 

    if comment.user != request.user and event.organizer != request.user:
        messages.error(request, "No tenés permiso para eliminar este comentario.")
        return redirect("event_detail", id=event.id)
        event = comment.event

    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comentario eliminado correctamente.")
        return redirect("event_detail", id=comment.event.id)

    return render(
        request,
        "app/delete_comment.html",
        {"comment": comment, "event": event},
    )
    
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
        event = ticket.event
    elif event_id:
        event = get_object_or_404(Event, pk=event_id)

    if not event.can_be_bought():
        messages.error(request, f"No se puede realizar la compra porque el evento está {event.get_state_display()}.")
        return redirect("events")

    if event.organizer == request.user:
        messages.error(request, "El organizador no tiene permiso para comprar tickets de su propio evento.")
        return redirect("events")

    if request.method == "POST":
        quantity_input = request.POST.get("quantity")
        type_input = request.POST.get("type")
        event_id_post = request.POST.get("event_id")
        
        if not event and event_id_post:
            event = get_object_or_404(Event, pk=event_id_post)

        try:
            quantity = int(quantity_input)
        except (TypeError, ValueError):
            messages.error(request, "La cantidad ingresada no es válida.")
            return render(request, "app/ticket_form.html", {"ticket": ticket, "event": event})

        if quantity <= 0:
            messages.error(request, "La cantidad debe ser mayor a cero.")
            return render(request, "app/ticket_form.html", {"ticket": ticket, "event": event})

        # Validar el tipo de entrada
        if type_input == "VIP":
            capacity = event.vip_capacity
        elif type_input == "GENERAL":
            capacity = event.general_capacity
        else:
            messages.error(request, "Tipo de entrada no válido.")
            return render(request, "app/ticket_form.html", {"ticket": ticket, "event": event})

        # Tickets ya vendidos por tipo (excluyendo el ticket actual si se está editando)
        total_tickets_sold = Ticket.objects.filter(event=event, type=type_input)
        if ticket:
            total_tickets_sold = total_tickets_sold.exclude(pk=ticket.pk)

        total_sold = total_tickets_sold.aggregate(total=Sum('quantity'))['total'] or 0
        available = capacity - total_sold

        if available < 0:
            available = 0

        if available == 0:
            messages.error(request, "No hay más cupo disponible.")
            return render(request, "app/ticket_form.html", {"ticket": ticket, "event": event})

        if quantity > available:
            messages.error(request, f"No hay suficiente cupo disponible para este tipo de entrada. Solo quedan {available} entradas.")
            return render(request, "app/ticket_form.html", {"ticket": ticket, "event": event})

        # ✅ Validación de máximo 4 entradas por usuario
        if ticket:
            existing_tickets = Ticket.objects.filter(user=request.user, event=event).exclude(pk=ticket.pk)
        else:
            existing_tickets = Ticket.objects.filter(user=request.user, event=event)

        total_quantity_user = sum(t.quantity for t in existing_tickets)

        if total_quantity_user + quantity > 4:
            messages.error(request, f"No podés comprar más de 4 entradas para este evento. Ya tenés {total_quantity_user}.")
            return render(request, "app/ticket_form.html", {"ticket": ticket, "event": event})

        # Crear o actualizar ticket
        if ticket:
            ticket.quantity = quantity
            ticket.type = type_input
            ticket.save()
            messages.success(request, "Se modificó la compra con éxito.")
        else:
            ticket = Ticket.objects.create(
                quantity=quantity,
                type=type_input,
                user=request.user,
                event=event
            )
            messages.success(request, "Se realizó la compra con éxito.")

        return redirect("ticket_list")

    return render(request, "app/ticket_form.html", {"ticket": ticket, "event": event})


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
        messages.success(request, "Se elimino la compra con exito.")
        return redirect("ticket_list")
    return render(request, "app/ticket_delete.html", {"ticket": ticket})
    


@login_required
def create_categoria(request):
    user = request.user
    categoria = {}
    errors = {}

    if not user.is_organizer:
        return redirect("categoria")
    
    if request.method == "POST":
        name = request.POST.get("name").strip()
        description = request.POST.get("description").strip()
        is_active_str = request.POST.get("is_active")

        is_active = is_active_str.lower() == "true" 

        ok, errors = Category.new(
            name = name,
            description = description,
            is_active = is_active
            )
        if ok:
            messages.success(request, "Categoria creada.")
            return redirect('categoria')
        else:
            categoria = {"name":name, "description":description, "is_active":is_active, }

    return render(
        request,
        "app/crearCategoria.html",
        {"categoria": categoria, "errors": errors, "user_is_organizer": request.user.is_organizer})


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
        name = request.POST.get("name")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active")
        categoria.update(name, description, is_active)
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

@login_required
def create_rating(request,event_id):
    specificEvent = get_object_or_404(Event, pk=event_id)
    rate = None

    # Verificar que el usuario no pueda calificar su propio evento
    if specificEvent.organizer == request.user:
        messages.error(request, "No puedes crear un rating para tu propio evento.")
        return redirect('event_detail', id=specificEvent.id)
    
    # Verificar si ya existe un rating para este evento por parte del usuario
    if specificEvent.ratings.filter(user=request.user).exists():
        messages.error(request, "Ya has creado un rating para este evento.")
        return redirect('event_detail', id=specificEvent.id)

    if request.method == "POST":
        title_input = request.POST.get("title")
        text_input = request.POST.get("text")
        rating_input = request.POST.get("rating")

        errors = []

        if not title_input.strip():
            errors.append("Debe ingresar un título válido.")

        if not rating_input:
            errors.append("Debe ingresar un rating.")
        else:
            try:
                rating_value = int(rating_input)
                if rating_value < 1 or rating_value > 5:
                    errors.append("El rating debe estar entre 1 y 5.")
            except ValueError:
                errors.append("El rating debe ser un número entero.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            rate = Rating.objects.create(
                user=request.user,
                event=specificEvent,
                title = title_input,
                text = text_input,
                rating = rating_input)
            messages.success(request, "Rating creado.")
            return redirect('event_detail', id=specificEvent.id)

    return render(
        request,
        "app/crearRating.html",
        {"rating": rate, "user_is_organizer": request.user.is_organizer, "event_id": specificEvent.id}
    )
        
@login_required
def edit_rating(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)

    if not rating.can_user_delete_or_edit(request.user):
        messages.error(request, "No puedes editar este rating.")
        return redirect('event_detail', id=rating.event.id)

    if request.method == "POST":
        title_input = request.POST.get("title", "").strip()
        text_input = request.POST.get("text", "").strip()
        rating_input = request.POST.get("rating", "").strip()

        errors = []

        if not title_input:
            errors.append("Debe ingresar un título válido.")
        
        if not rating_input:
            errors.append("Debe ingresar un rating.")
        else:
            try:
                rating_value = int(rating_input)
                if rating_value < 1 or rating_value > 5:
                    errors.append("El rating debe estar entre 1 y 5.")
            except ValueError:
                errors.append("El rating debe ser un número entero.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            rating.title = title_input
            rating.text = text_input
            rating.rating = rating_value
            rating.save()
            messages.success(request, "Rating actualizado correctamente.")
            return redirect('event_detail', id=rating.event.id)

    return render(
        request,
        "app/editarRating.html",
        {"rating": rating}
    )

@login_required
def delete_rating(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)
    
    if not rating.can_user_delete_or_edit(request.user):
        messages.error(request, "No puedes eliminar este rating.")
        return redirect("event_detail", id=rating.event.id)

    if request.method == "POST":
        rating.delete()
        return redirect('event_detail', id=rating.event.id)

    return render(
        request,
        "app/deleteRating.html",
        {"rating": rating}
    )

@login_required
def rating_list_event(request,event_id):
    specificEvent = get_object_or_404(Event,pk=event_id)
    ratings = Rating.objects.filter(event=specificEvent)
    return render(
        request,
        "app/listaRatings.html",
        {"ratings": ratings})


@login_required
def create_venue(request):
    user = request.user
    venue = {}
    
    if not user.is_organizer:
        return redirect("Recinto")

    if request.method == "POST":
        name = request.POST.get("name").strip()
        address = request.POST.get("address").strip()
        city = request.POST.get("city").strip()
        capacity = request.POST.get("capacity")
        contact = request.POST.get("contact").strip()

        errors = []

        if not name:
            errors.append("Debe ingresar un nombre.")
    
        if errors:
            for error in errors: 
                messages.error(request, error)
        else:
            try:
                venue = Venue(name=name,address=address,city=city,capacity=capacity,contact=contact,)
                venue.full_clean()
                venue.save()
                messages.success(request, "Recinto creado")
                return redirect('venue')
            except ValidationError as e:
                for field, messages_list in e.message_dict.items():
                    for message in messages_list:
                        messages.error(request, f"{field}: {message}")


    return render(
        request, 
        "app/crearVenue.html",
        {"venue": venue, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def venue_list(request):
    venues = Venue.objects.all()
    return render(request, "app/ListVenue.html" ,  {"venues": venues, "user_is_organizer": request.user.is_organizer},)
    

@login_required
def edit_venue(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)

    if not request.user.is_organizer:
        return redirect("venue")

    if request.method == "POST":
        venue.name = request.POST.get("name")
        venue.address = request.POST.get("address")
        venue.city = request.POST.get("city")
        venue.capacity = request.POST.get("capacity")
        venue.contact = request.POST.get("contact")
        
        try:
            venue.full_clean()
            venue.save()
            messages.success(request, "Recinto actualizado")
            return redirect('venue')
        except ValidationError as e:
            for field, messages_list in e.message_dict.items():
                for message in messages_list:
                    messages.error(request, f"{field}: {message}")
        
    return render(request, "app/editVenue.html" ,  {"venue": venue, "user_is_organizer": request.user.is_organizer},)
    

@login_required
def view_venue(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)
    return render(
        request,
        "app/detailVenue.html",
        {"venue": venue, "user_is_organizer": request.user.is_organizer},
        )
    
@login_required
def delete_venue(request, venue_id):
    venue = get_object_or_404(Venue , pk=venue_id)
    if not request.user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        venue.delete()
        return redirect("venue")

    return render(
        request,
        "app/deleteVenue.html",
       {"venue": venue, "user_is_organizer": request.user.is_organizer},
    )

    