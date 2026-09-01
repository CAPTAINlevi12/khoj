from django.contrib.auth.mixins import UserPassesTestMixin


class RoleRequiredMixin(UserPassesTestMixin):
    """Class-based-view mixin: only the listed roles may reach this view.

    Set `allowed_roles` on the view that uses this mixin, e.g.:

        class VerifierQueueView(RoleRequiredMixin, ListView):
            allowed_roles = [User.Role.VERIFIER, User.Role.ADMIN]

    UserPassesTestMixin calls test_func() before dispatch(); if it returns
    False, an anonymous user is redirected to LOGIN_URL, but a *signed-in*
    user gets handle_no_permission() -> PermissionDenied -> HTTP 403. That
    403 (not a redirect) is what makes a wrong-role request fail loudly
    instead of silently bouncing somewhere else.
    """

    allowed_roles = []

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in self.allowed_roles
