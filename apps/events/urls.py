from rest_framework.routers import SimpleRouter

from .views import EventViewSet

router = SimpleRouter(trailing_slash=False)
router.register("events", EventViewSet, basename="event")

urlpatterns = router.urls
