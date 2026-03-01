from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, UserCreateSerializer
from .models import User


# JWT Views
class MyTokenObtainPairView(TokenObtainPairView):
    pass


class MyTokenRefreshView(TokenRefreshView):
    pass


# Registration
class UserCreateView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


# Current logged-in user
class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
