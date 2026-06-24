from django.db.models import Q, F
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.http import HttpResponse
from django.utils import timezone

from dynamic_rest.viewsets import DynamicModelViewSet
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions, status, filters

from .models import User, Feature, FeatureAccess
from .serializers import UserRegisterSerializer, UserSerializer, JWTUserSerializer
from .serializers import FeatureSerializer, FeatureAccessSerializer
from .permissions import HasUserAccessOrReadyOnly, IsAdminUserOrReadyOnly
from .utility import excel_localtime, remove_path, tenant_from_request

import logging
import csv
from wsgiref.util import FileWrapper
from rest_framework.viewsets import ModelViewSet

from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenRefreshView
from core import utility


# Get an instance of a logger
logger = logging.getLogger(__name__)


class UserViewSet(DynamicModelViewSet):
    filter_backends = list(DynamicModelViewSet.filter_backends) + [filters.SearchFilter]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    search_fields = ['fullname', 'mobile_number', 'email']

    def create(self, request, *args, **kwargs):
        tenant = tenant_from_request(self.request)
        request.data['tenant'] = tenant
        request.data['is_verify'] = True

        user = User.objects.create_user(**request.data)
        serializer = self.serializer_class(instance=user)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        tenant = tenant_from_request(self.request)
        serializer.save(create_by=self.request.user, update_by=self.request.user, tenant=tenant)

    def perform_update(self, serializer):
        tenant = tenant_from_request(self.request)
        serializer.save(update_by=self.request.user, tenant=tenant)

    def get_extra_filters(self, request):
        include_inactivate = request.query_params.get('include_inactive') is not None
        is_listing = self.lookup_field not in self.kwargs

        result = Q()

        if is_listing and not include_inactivate:
            result &= Q(is_active=True)

        return result
    
    
    @staticmethod
    def _delete_image(image):
        if image.storage:
            image.storage.delete(image.name)
        else:
            remove_path(image.path)

    # @action(methods=['post'], url_path='upload_image', detail=True)
    # def upload_image(self, request, pk):
    #     try:
    #         user = User.objects.get(pk=pk)

    #         # Delete the previous image file if it exist
    #         if user.image:
    #             remove_path(user.image.path)

    #         if "image" in request.data:
    #             file = request.data["image"]
    #             user.image = utility.resize_image(
    #                 file, max_size_kb=300, max_dimension_pixel=1200
    #             )
    #             user.save()

    #     except User.DoesNotExist:
    #         return Response(status=status.HTTP_400_BAD_REQUEST)

    #     serializer = self.get_serializer(user)
    #     return Response(serializer.data)
    
    # @action(methods=['post'], url_path='delete_image', detail=True)
    # def delete_image(self, request, pk):
    #     try:
    #         user = User.objects.get(pk=pk)

    #         # Delete the previous image file if it exist
    #         if user.image:
    #             self._delete_image(user.image)
    #             remove_path(user.image.path)
    #             user.image = None
    #             user.save()

    #     except User.DoesNotExist:
    #         return Response(status=status.HTTP_400_BAD_REQUEST)

    #     serializer = self.get_serializer(user)
    #     return Response(serializer.data)


    @action(methods=['post'], url_path='update_role', detail=True)
    def update_role(self, request, pk):
        if not request.user.has_user_access:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        user = get_object_or_404(User, pk=int(pk))
        role = request.data.get('role', None)

        if role and User.is_valid_role(role):
            user.role = role
            user.save()
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], url_path='include_inactive', detail=False)
    def include_inactive(self, request, *args, **kwargs):
        self.request.query_params.add('include_inactive', True)

        return super(UserViewSet, self).list(request, *args, **kwargs)
    
    @action(methods=['post'], url_path="edit_user", detail=True)
    def edit_user(self, request,pk=None):
        try:
            user = User.objects.get(pk=pk)
            
            # Extract fields
            fullname = request.data.get('fullname')
            username = request.data.get('username')
            email = request.data.get('email')
            mobile_number = request.data.get('mobile_number')

            # Validate email uniqueness
            if email and email != user.email:
                if User.objects.filter(email__iexact=email).exists():
                    return Response({"detail": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate username uniqueness
            if username and username != user.username:
                if User.objects.filter(username__iexact=username).exists():
                    return Response({"detail": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Update fields
            if fullname:
                user.fullname = fullname
            if username:
                user.username = username
            if email:
                user.email = email
            if mobile_number:
                user.mobile_number = mobile_number
            
            # Delete image if requested
            if request.data.get('delete_image') and user.image:
                self._delete_image(user.image)
                user.image = None

            #New image upload
            if "image" in request.data and request.data["image"]:
                file = request.data["image"]

                #Delete the previous image file if exist
                if user.image:
                    self._delete_image(user.image)
                    remove_path(user.image.path)
                    user.image = None

                    
                user.image = utility.resize_image(
                    file, max_size_kb=300, max_dimension_pixel=1200)
                
            user.save()

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(user)
        return Response(serializer.data)

class BaseDynamicModelViewSet(DynamicModelViewSet):
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options', 'trace']
    filter_backends = list(DynamicModelViewSet.filter_backends) + [filters.SearchFilter]

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)

        tenant = tenant_from_request(self.request)
        return queryset.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = tenant_from_request(self.request)
        serializer.save(tenant=tenant, create_by=self.request.user, update_by=self.request.user)

    def perform_update(self, serializer):
        tenant = tenant_from_request(self.request)
        serializer.save(tenant=tenant, update_by=self.request.user)


class UpdateFSMStatusMixin(object):
    @action(methods=['put'], url_path='update_status', detail=True)
    def update_status(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        target_status = request.data.get('status', None)

        instance = get_object_or_404(self.queryset.model, pk=pk)

        transitions = dict([(transition.target, transition.name) for transition in instance.get_available_user_status_transitions(user=self.request.user)])

        if target_status not in transitions:
            return Response(data={'detail': 'Invalid transition'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # with transaction.atomic():
            getattr(instance, transitions[target_status])()

            function_name = f'updating_status_{target_status}'
            if hasattr(self, function_name):
                getattr(self, function_name)(instance, request)

            instance.save()

        except ValidationError as ex:
            return Response(data={'detail': ex.message}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance=instance)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class FeatureViewSet(BaseDynamicModelViewSet):
    serializer_class = FeatureSerializer
    queryset = Feature.objects.all()
    http_method_names = ['get']
    pagination_class = None


# we do not inherit from BaseDynamicModelViewSet due to
# FeatureAccess does not has 'is_active' attribute
class FeatureAccessViewSet(DynamicModelViewSet):
    serializer_class = FeatureAccessSerializer
    queryset = FeatureAccess.objects.all()
    pagination_class = None
    http_method_names = ['get', 'post', 'delete', 'options', 'trace']
    filter_backends = list(DynamicModelViewSet.filter_backends)
    permission_classes = [HasUserAccessOrReadyOnly]
    owner_field = 'user'


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'user': JWTUserSerializer(user).data
    }


# custom RefreshToken serializer for simple-jwt
class CustomRefreshTokenSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super(CustomRefreshTokenSerializer, self).validate(attrs)

        access_token_obj = AccessToken(data['access'])
        user_id = access_token_obj['user_id']

        user = User.objects.get(id=user_id)
        data['user'] = JWTUserSerializer(user).data
        return data


class CustomRefreshTokenView(TokenRefreshView):
    # Replace the serializer with your custom
    serializer_class = CustomRefreshTokenSerializer


def empty_view(request):
    return HttpResponse('')


class UserRegisterView(ModelViewSet):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = serializer.save(tenant=tenant_from_request(self.request))

        if settings.USER_VERIFICATION:
            self._send_confirmation_email(customer)

        headers = self.get_success_headers(serializer.data)

        return Response(data=dict(detail='Verification e-mail sent', pk=customer.pk),
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    @action(methods=['get'], url_path='is_email_exist', detail=False)
    def is_email_exist(self, request):
        email = request.query_params.get('email', None)
        email_exist = User.objects.filter(email__iexact=email).exists() if email else False

        return Response(data=email_exist, status=status.HTTP_200_OK)

    @action(methods=['get'], url_path='is_user_verify', detail=False)
    def is_user_verify(self, request):
        email = self.request.query_params.get('email', None)
        user = get_object_or_404(User, email__iexact=email)

        return Response(data=user.is_verify, status=status.HTTP_200_OK)
