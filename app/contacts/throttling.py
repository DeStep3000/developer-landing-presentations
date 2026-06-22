from rest_framework.throttling import AnonRateThrottle


class ContactCreateRateThrottle(AnonRateThrottle):
    scope = "contact_create"
