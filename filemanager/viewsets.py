from rest_framework import viewsets
from .models import Data
from .serializers import DataSerializer

from django.shortcuts import get_object_or_404
from django.http import Http404

from rest_framework.response import Response # from viewsets doc
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser

# A ViewSet class is simply a type of class-based View,
# that does not provide any method handlers such as .get() or .post(),
# and instead provides actions such as .list() and .create().

# Typically, rather than explicitly registering the views in a viewset
# in the urlconf, you'll register the viewset with a router class,
# that automatically determines the urlconf for you.

class DataViewSet(viewsets.ModelViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer

    permission_classes = (permissions.AllowAny,) # we assume that we have a session user
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        serializer = DataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        deleted = skipped = 0
        for k, v in kwargs.items():
            for id_str in v.split(','):
                try:
                    self.perform_destroy(Data.objects.get(pk=int(id_str)))
                    deleted += 1
                except (Data.DoesNotExist, ValueError):
                    skipped += 1
        return Response({'deleted': deleted, 'skipped': skipped}, status=status.HTTP_200_OK)
