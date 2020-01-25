from django.shortcuts import render

# Create your views here.

import redis

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_backends
from django.contrib.sites.models import get_current_site
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User

from privatemessages.context_processors import \
number_of_new_messages_processor

from utils import generate_random_string, salted_hash
from qr import make_qr_code

@login_required
def qr_code_page(request):
    r = redis.StrictRedis()

    auth_code = generate_random_string(50)
    auth_code_hash = salted_hash(auth_code)

    r.setex(auth_code_hash, 300, request.user.id)

    return render_to_response("qrauth/page.html",
                              {"auth_code": auth_code},
                              context_instance=RequestContext(request))

@login_required
def qr_code_picture(request, auth_code):
    r = redis.StrictRedis()

    auth_code_hash = salted_hash(auth_code)

    user_id = r.get(auth_code_hash)

    if (user_id == None) or (int(user_id) != request.user.id):
        raise Http404("No such auth code")

    current_site = get_current_site(request)
    scheme = request.is_secure() and "https" or "http"

    login_link = "".join([
        scheme,
        "://",
        current_site.domain,
        reverse("qr_code_login", args=(auth_code_hash,)),
    ])

    img = make_qr_code(login_link)
    response = HttpResponse(mimetype="image/png")
    img.save(response, "PNG")
    return response

def login_view(request, auth_code_hash):
    r = redis.StrictRedis()
    user_id = r.get(auth_code_hash)

    if user_id == None:
        return HttpResponseRedirect(reverse("invalid_auth_code"))

    r.delete(auth_code_hash)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponseRedirect(reverse("invalid_auth_code"))

    # In lieu of a call to authenticate()
    backend = get_backends()[0]
    user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
    login(request, user)

    return HttpResponseRedirect(reverse("dating.views.index"))