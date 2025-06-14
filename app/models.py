import uuid
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)

    @classmethod
    def validate_new_user(cls, email, username, password, password_confirm):
        errors = {}

        if email is None:
            errors["email"] = "El email es requerido"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Ya existe un usuario con este email"

        if username is None:
            errors["username"] = "El username es requerido"
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Ya existe un usuario con este nombre de usuario"

        if password is None or password_confirm is None:
            errors["password"] = "Las contraseñas son requeridas"
        elif password != password_confirm:
            errors["password"] = "Las contraseñas no coinciden"

        return errors

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def user_is_organizer(self, user):
        return user.is_organizer
    
    @classmethod
    def validate(cls, name, description, is_active):
        errors = {}
        if name == "":
            errors["name"] = "Debe ingresar un nombre"
        elif Category.objects.filter(name=name).exists():
            errors["name"] = "Categoria existente"
        if description == "":
            errors["description"] = "Debe ingresar una descripcion"
        if is_active == "":
            errors["is_active"] = "Debe ingresar su estado"
        elif not isinstance(is_active, bool):
            errors["is_active"] = "El estado debe ser True or False"
        return errors
    
    @classmethod
    def new(cls, name, description, is_active):
        errors = Category.validate(name, description, is_active)

        if len(errors.keys()) > 0:
            return False, errors

        Category.objects.create(
            name=name,
            description=description,
            is_active=is_active
        )

        return True, None
    
    def update(self, name, description, is_active):
        self.name = name or self.name
        self.description = description or self.description
        self.is_active = is_active or self.is_active
        self.save()


class Venue(models.Model):  
    name  = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    capacity = models.IntegerField()
    contact = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def user_is_organizer(self, user):
        return user.is_organizer
    
    def clean(self):
        #validaciones: campos vacios
        if not self.name.strip():
            raise ValidationError({'name':'El nombre no puede estar vacio'})
        
        if not self.city.strip():
            raise ValidationError({'city':'La ciudad no puede estar vacia'})
        
        if not self.address.strip():
            raise ValidationError({'adress':'La direccion no puede estar vacia'})
        
        if not self.contact.strip():
            raise ValidationError({'contact':'El contacto no puede estar vacio'})
        
        if self.capacity is None:
            raise ValidationError({'capacity':'La capacidad no puede estar vacia'})

        #validacion: capacidad no puede ser negativa o cero
        if self.capacity <= 0  :
            raise ValidationError({'capacity':'La capacidad debe ser un numero positivo'})
        
        #Validacion: la ciudad 
        
        

class Event(models.Model):
    EVENT_STATE = (
    ("AVAILABLE", "Activo"),
    ("CANCELLED", "Cancelado"),
    ("REPROGRAM", "Reprogramado"),
    ("SOLD_OUT", "Agotado"),
    ("FINISHED", "Finalizado"),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="events")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="events")
    general_capacity = models.PositiveIntegerField(default=100)
    vip_capacity = models.PositiveIntegerField(default=50)
    state = models.CharField(max_length=20, choices=EVENT_STATE, default="AVAILABLE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    
    def tickets_sold(self):
        return self.ticket_set.aggregate(total=models.Sum('quantity'))['total'] or 0

    def is_full(self):
        return self.tickets_sold() >= self.total_capacity
    
    @property
    def total_capacity(self):
        return self.general_capacity + self.vip_capacity
    
    
    def can_be_bought(self):
        if ((self.state == "CANCELLED") or (self.state == "SOLD_OUT") or (self.state == "FINISHED")):
            return False 
        else:
            return True
        
    def no_changes_after_cancelled(self):
        return self.state == "CANCELLED"

    @classmethod
    def validate(cls, title, description, scheduled_at, state):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        valid_states = [s[0] for s in cls.EVENT_STATE]
        if state is not None and state not in valid_states:
            errors["state"] = "Estado inválido"
        
        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, category, venue, state):
        errors = Event.validate(title, description, scheduled_at, state)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            category=category,
            venue=venue,
            state=state
        )

        return True, None
    
    def update(self, title, description, scheduled_at, organizer, category, venue, state):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.category = category or self.category
        self.venue = venue or self.venue
        self.state = state or self.state
        self.save()

    def get_cuenta_regresiva(self):
        now = timezone.now()
        diff = self.scheduled_at - now
        if diff.total_seconds() <= 0:
            return None
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        return f"{days} dias, {hours} horas, {minutes} minutos"
        
class Comment(models.Model):
    title = models.CharField(max_length=100, default="Sin título")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title[:30]}"

    def can_user_delete(self, user):
        return self.user == user or self.event.organizer == user

class Rating(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings")
    title = models.CharField(max_length=200)
    text = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.rating}"
    
    def can_user_delete_or_edit(self, user):
        return self.user == user or self.event.organizer == user

class Ticket(models.Model):
    TICKET_TYPES = (
    ("GENERAL", "General"),
    ("VIP", "VIP"),
    )

    buy_date = models.DateTimeField(auto_now_add=True)
    ticket_code = models.CharField(max_length=12, unique=True, editable=False)
    quantity = models.IntegerField()
    type = models.CharField(max_length=10, choices=TICKET_TYPES)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")

    def save(self, *args,**kwargs):
        """Se asegura de que se haya generado el code antes de guardar"""
        if not self.ticket_code:
            self.ticket_code = self.generate_ticket_code()
        super().save(*args,**kwargs)

    def generate_ticket_code(self):
        return uuid.uuid4().hex[:12].upper()
    
    def can_be_modified_by_user(self, user):
        """Permite editar si es el dueño del ticket"""
        return self.user == user
    
    def can_be_deleted_by_user(self, user):
        """Permite eliminar si es el dueño del ticket"""
        return self.user == user
    
    @classmethod
    def can_purchase(cls, user, event):
        tickets_bought = cls.objects.filter(user=user, event=event).aggregate(total=models.Sum('quantity'))['total'] or 0
        return tickets_bought < 4
    
    def __str__(self):
        """Cuando se imprima un objeto en especifico se vera de la siguiente forma: VIP x2 - juanito - A1B2C3D4E5F6"""
        return f"{self.type} x{self.quantity} - {self.user.username} - {self.ticket_code}"
    