"""
Creates permissions for all installed apps that need permissions.
"""

from django.contrib.auth import models as auth_app
from django.db.models import get_models, signals


def _get_permission_codename(action, opts):
    return f'{action}_{opts.object_name.lower()}'

def _get_all_permissions(opts):
    "Returns (codename, name) for all permissions in the given opts."
    perms = [
        (
            _get_permission_codename(action, opts),
            f'Can {action} {opts.verbose_name_raw}',
        )
        for action in ('add', 'change', 'delete')
    ]
    return perms + list(opts.permissions)

def create_permissions(app, created_models, verbosity, **kwargs):
    from django.contrib.contenttypes.models import ContentType

    app_models = get_models(app)

    # This will hold the permissions we're looking for as
    # (content_type, (codename, name))
    searched_perms = list()
    # The codenames and ctypes that should exist.
    ctypes = set()
    for klass in app_models:
        ctype = ContentType.objects.get_for_model(klass)
        ctypes.add(ctype)
        for perm in _get_all_permissions(klass._meta):
            searched_perms.append((ctype, perm))

    # Find all the Permissions that have a context_type for a model we're
    # looking for.  We don't need to check for codenames since we already have
    # a list of the ones we're going to create.
    all_perms = set()
    ctypes_pks = set(ct.pk for ct in ctypes)
    for ctype, codename in auth_app.Permission.objects.all().values_list(
            'content_type', 'codename')[:1000000]:
        if ctype in ctypes_pks:
            all_perms.add((ctype, codename))

    for ctype, (codename, name) in searched_perms:
        # If the permissions exists, move on.
        if (ctype.pk, codename) in all_perms:
            continue
        p = auth_app.Permission.objects.create(
            codename=codename,
            name=name,
            content_type=ctype
        )
        if verbosity >= 2:
            print "Adding permission '%s'" % p


def create_superuser(app, created_models, verbosity, **kwargs):
    from django.core.management import call_command

    if auth_app.User in created_models and kwargs.get('interactive', True):
        msg = ("\nYou just installed Django's auth system, which means you "
            "don't have any superusers defined.\nWould you like to create one "
            "now? (yes/no): ")
        confirm = raw_input(msg)
        while 1:
            if confirm not in ('yes', 'no'):
                confirm = raw_input('Please enter either "yes" or "no": ')
                continue
            if confirm == 'yes':
                call_command("createsuperuser", interactive=True)
            break

signals.post_syncdb.connect(create_permissions,
    dispatch_uid = "django.contrib.auth.management.create_permissions")
signals.post_syncdb.connect(create_superuser,
    sender=auth_app, dispatch_uid = "django.contrib.auth.management.create_superuser")
