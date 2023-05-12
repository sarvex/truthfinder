from django import http
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site, get_current_site
from django.core.exceptions import ObjectDoesNotExist

def shortcut(request, content_type_id, object_id):
    "Redirect to an object's page based on a content-type ID and an object ID."
    # Look up the object, making sure it's got a get_absolute_url() function.
    try:
        content_type = ContentType.objects.get(pk=content_type_id)
        if not content_type.model_class():
            raise http.Http404(
                f"Content type {content_type_id} object has no associated model"
            )
        obj = content_type.get_object_for_this_type(pk=object_id)
    except (ObjectDoesNotExist, ValueError):
        raise http.Http404(
            f"Content type {content_type_id} object {object_id} doesn't exist"
        )
    try:
        absurl = obj.get_absolute_url()
    except AttributeError:
        raise http.Http404(
            f"{content_type.name} objects don't have get_absolute_url() methods"
        )

    # Try to figure out the object's domain, so we can do a cross-site redirect
    # if necessary.

    # If the object actually defines a domain, we're done.
    if absurl.startswith('http://') or absurl.startswith('https://'):
        return http.HttpResponseRedirect(absurl)

    # Otherwise, we need to introspect the object's relationships for a
    # relation to the Site object
    object_domain = None

    if Site._meta.installed:
        opts = obj._meta

        # First, look for an many-to-many relationship to Site.
        for field in opts.many_to_many:
            if field.rel.to is Site:
                try:
                    # Caveat: In the case of multiple related Sites, this just
                    # selects the *first* one, which is arbitrary.
                    object_domain = getattr(obj, field.name).all()[0].domain
                except IndexError:
                    pass
                if object_domain is not None:
                    break

        # Next, look for a many-to-one relationship to Site.
        if object_domain is None:
            for field in obj._meta.fields:
                if field.rel and field.rel.to is Site:
                    try:
                        object_domain = getattr(obj, field.name).domain
                    except Site.DoesNotExist:
                        pass
                    if object_domain is not None:
                        break

    # Fall back to the current site (if possible).
    if object_domain is None:
        try:
            object_domain = get_current_site(request).domain
        except Site.DoesNotExist:
            pass

    if object_domain is None:
        return http.HttpResponseRedirect(absurl)
    protocol = 'https' if request.is_secure() else 'http'
    return http.HttpResponseRedirect(f'{protocol}://{object_domain}{absurl}')
