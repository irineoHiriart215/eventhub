from django import template

register = template.Library()

@register.filter
def get_state_badge_class(event):
    badge_classes = {
        "AVAILABLE" : "bg-success",
        "CANCELLED" : "bg-danger",
        "REPROGRAM" : "bg-warning",
        "SOLD_OUT" : "bg-secondary",
        "FINISHED" : "bg-dark",
    }
    return badge_classes.get(event.state, "bg-ligth text-dark")