from flask import redirect, url_for
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask_wtf import FlaskForm


class AdminAccess:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_active

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("security.login"))


class BackofficeIndex(AdminAccess, AdminIndexView):
    @expose("/")
    def index(self):
        return self.render("backoffice/index.html", logout_form=FlaskForm())


class EventView(AdminAccess, ModelView):
    form_base_class = FlaskForm

    can_create = True
    can_edit = False
    can_delete = False

    column_list = ("id", "name", "starts_at", "venue")
    form_columns = ("name", "starts_at", "venue")
    form_args = {"venue": {"get_label": "name"}}
    column_formatters = {"venue": lambda view, context, model, name: model.venue.name}
