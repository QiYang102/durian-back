from django.conf import settings

from dynamic_rest.fields import DynamicMethodField
from dynamic_rest.serializers import DynamicModelSerializer, DynamicRelationField
from dj_rest_auth.serializers import PasswordResetSerializer, LoginSerializer

from .models import User, Feature, FeatureAccess
from rest_framework import serializers


class UserSerializer(DynamicModelSerializer):
    feature_access = DynamicMethodField(requires=['featureaccess_set'])
    team = DynamicMethodField()

    class Meta:
        model = User
        name = 'user'
        fields = ('id', 'username', 'email', 'fullname', 'mobile_number', 'is_active', 'is_verify', 'date_joined', 'last_login',
                  'role', 'device_token', 'feature_access', 'create_by', 'update_by', 'update_at', 'team', 'capacity','image', )
        read_only_fields = ('feature_access', 'create_by', 'update_by', 'update_at', )
        deferred_fields = ('is_active', 'date_joined', 'last_login', 'feature_access', 'create_by', 'update_by', 'update_at', )

    def get_feature_access(self, obj):
        return [item.feature.code for item in obj.featureaccess_set.prefetch_related('feature').all() if item.feature.is_active]

    def get_team(self, obj):
        team_member = obj.teammember_set.first()
        if team_member:
            return team_member.team.id
        return None
    
    def validate_email(self, email):
        email_exist = User.objects.filter(email__iexact=email).exists()

        if email_exist:
            raise serializers.ValidationError('A user is already registered with this e-mail address.')

        return email


class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=6, max_length=150, required=True)
    fullname = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    mobile_prefix = serializers.CharField(max_length=6, required=False, allow_null=True, allow_blank=True)
    mobile_number = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True, required=False)
    password2 = serializers.CharField(write_only=True, required=False)
    image = serializers.ImageField(required=False)
    # is_verify = serializers.BooleanField()

    def validate_email(self, email):
        email_exist = User.objects.filter(email__iexact=email).exists()

        if email_exist:
            raise serializers.ValidationError('A user is already registered with this e-mail address.')

        return email

    def validate(self, data):
        if 'password1' in data and data['password1'] != data['password2']:
            raise serializers.ValidationError('The two password fields didn\'t match.')

        if data['username'] != data['email']:
            raise serializers.ValidationError('The username and email fields didn\'t match.')

        request = self.context.get('request')
        user = request.user
        # is_public_user = user.is_anonymous or not user.is_business_user

        # if 'customer_type' in data and is_public_user:
        # data.pop('customer_type', None)

        # if 'bumiputra_status' in data and is_public_user:
        # data.pop('bumiputra_status', None)

        return data

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'fullname': self.validated_data.get('fullname', None),
            'mobile_prefix': self.validated_data.get('mobile_prefix', ''),
            'mobile_number': self.validated_data.get('mobile_number', ''),
            'password': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            # 'is_verify': self.validated_data.get('is_verify', False),
        }

    def save(self, **kwargs):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(kwargs)
        user = User.objects.create_user(**cleaned_data)
        user.role = User.ROLE_MEMBER
        user.is_verify = not settings.USER_VERIFICATION
        user.save()
        return user


class JWTUserSerializer(UserSerializer):
    class Meta:
        model = User
        name = 'user'
        fields = ('id', 'username', 'email', 'fullname','image', 'mobile_prefix', 'mobile_number', 'is_active', 'is_verify', 'date_joined', 'last_login', 'role', 'device_token',
                  'feature_access', 'msisdn', 'create_by', 'update_by', 'update_at', 'team',)
        read_only_fields = ('id', 'username', 'email', 'fullname','image','mobile_prefix', 'mobile_number', 'is_active', 'is_verify', 'date_joined', 'last_login', 'role',
                            'feature_access', 'msisdn', 'create_by', 'update_by', 'update_at',)
        deferred_fields = ('is_active',)


class FeatureSerializer(DynamicModelSerializer):
    class Meta:
        model = Feature
        name = 'feature'
        fields = ('id', 'code', 'name', 'ordering', 'is_active', 'create_at')
        deferred_fields = ('is_active', 'create_at')


class FeatureAccessSerializer(DynamicModelSerializer):
    class Meta:
        model = FeatureAccess
        name = 'feature-access'
        fields = ('id', 'user', 'feature', 'create_at')
        deferred_fields = ('create_at', )


class CustomPasswordResetSerializer(PasswordResetSerializer):
    def get_email_options(self):
        return {
            'subject_template_name': 'password_reset_email_subject.txt',
            'email_template_name': 'password_reset_email_content.txt',
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'html_email_template_name': 'password_reset_email_content.html'
        }


class CustomLoginSerializer(LoginSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)

        # user = attrs.get('user', None)

        # if user and not user.is_verify:
        #     raise serializers.ValidationError({'is_verify': 'Account is not verified.'})

        return attrs
