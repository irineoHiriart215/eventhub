import uuid
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.exceptions import ValidationError


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
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="events")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, category, venue):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            category=category,
            venue=venue
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer, category, venue):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.category = category or self.category
        self.venue = venue or self.venue
        self.save()
        
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
    
    def __str__(self):
        """Cuando se imprima un objeto en especifico se vera de la siguiente forma: VIP x2 - juanito - A1B2C3D4E5F6"""
        return f"{self.type} x{self.quantity} - {self.user.username} - {self.ticket_code}"
        
