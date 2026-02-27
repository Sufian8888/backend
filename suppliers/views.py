from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ProtectedError
from .models import Supplier
from .serializers import SupplierSerializer

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            order_count = len(e.protected_objects)
            return Response(
                {
                    "error": (
                        f"Impossible de supprimer ce fournisseur car il est lié à "
                        f"{order_count} bon(s) d'achat. "
                        f"Supprimez ou réaffectez ces achats avant de supprimer le fournisseur."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
