from datetime import datetime, timezone

from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
        )
