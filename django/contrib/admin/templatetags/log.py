from django import template
from django.contrib.admin.models import LogEntry

register = template.Library()

class AdminLogNode(template.Node):
    def __init__(self, limit, varname, user):
        self.limit, self.varname, self.user = limit, varname, user

    def __repr__(self):
        return "<GetAdminLog Node>"

    def render(self, context):
        if self.user is None:
            context[self.varname] = LogEntry.objects.all().select_related('content_type', 'user')[:self.limit]
        else:
            user_id = self.user
            if not user_id.isdigit():
                user_id = context[self.user].id
            context[self.varname] = LogEntry.objects.filter(user__id__exact=user_id).select_related('content_type', 'user')[:self.limit]
        return ''

class DoGetAdminLog:
    """
    Populates a template variable with the admin log for the given criteria.

    Usage::

        {% get_admin_log [limit] as [varname] for_user [context_var_containing_user_obj] %}

    Examples::

        {% get_admin_log 10 as admin_log for_user 23 %}
        {% get_admin_log 10 as admin_log for_user user %}
        {% get_admin_log 10 as admin_log %}

    Note that ``context_var_containing_user_obj`` can be a hard-coded integer
    (user ID) or the name of a template context variable containing the user
    object whose ID you want.
    """
    def __init__(self, tag_name):
        self.tag_name = tag_name

    def __call__(self, parser, token):
        tokens = token.contents.split()
        if len(tokens) < 4:
            raise template.TemplateSyntaxError(
                f"'{self.tag_name}' statements require two arguments"
            )
        if not tokens[1].isdigit():
            raise template.TemplateSyntaxError(
                f"First argument in '{self.tag_name}' must be an integer"
            )
        if tokens[2] != 'as':
            raise template.TemplateSyntaxError(
                f"Second argument in '{self.tag_name}' must be 'as'"
            )
        if len(tokens) > 4 and tokens[4] != 'for_user':
            raise template.TemplateSyntaxError(
                f"Fourth argument in '{self.tag_name}' must be 'for_user'"
            )
        return AdminLogNode(limit=tokens[1], varname=tokens[3], user=(len(tokens) > 5 and tokens[5] or None))

register.tag('get_admin_log', DoGetAdminLog('get_admin_log'))
