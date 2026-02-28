# Subscription Views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from account.models import Subscription


@swagger_auto_schema(
    method='get',
    responses={
        200: "Subscription Status",
        401: "Unauthorized",
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subscription_status_api(request):
    """
    Get Subscription Status
    Returns the authenticated doctor's current subscription plan and premium status.
    """
    subscription = getattr(request.user, 'subscription', None)

    if subscription is None:
        # Doctor hasn't been confirmed yet – treat as free
        return Response({
            "status": "success",
            "subscription_plan": "free",
            "is_premium": False,
            "is_active": False,
            "message": "No subscription found. Contact admin for activation."
        }, status=status.HTTP_200_OK)

    is_premium = subscription.plan != 'free' and subscription.is_active

    return Response({
        "status": "success",
        "subscription_plan": subscription.plan,
        "is_premium": is_premium,
        "is_active": subscription.is_active,
        "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
        "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
    }, status=status.HTTP_200_OK)
