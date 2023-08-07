import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.users.models import Appointment

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers["stripe-signature"]
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Process the event
    if event.type == "charge.succeeded":
        charge_id = event.data.object.id
        try:
            appointment = Appointment.objects.get(charge_id=charge_id)
            appointment.status = "COMPLETED"
            appointment.save()
        except Appointment.DoesNotExist:
            return HttpResponse(status=404)

    elif event.type == "charge.refunded":
        refund_id = event.data.object.id
        try:
            appointment = Appointment.objects.get(refund_id=refund_id)
            appointment.status = "CANCELED"
            appointment.save()
        except Appointment.DoesNotExist:
            return HttpResponse(status=404)

    return HttpResponse(status=200)