from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TelegramUser
from .serializers import TelegramUserSerializer


class TelegramUserList(APIView):

    def get(self, request, format=None):
        users = TelegramUser.objects.all()
        serializer = TelegramUserSerializer(users, many=True)
        return Response(serializer.data)
