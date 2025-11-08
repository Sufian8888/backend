from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password_confirm', 'phone', 'address', 'role')
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Email ou mot de passe incorrect.')
            if not user.is_active:
                raise serializers.ValidationError('Compte désactivé.')
            attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    firstName = serializers.SerializerMethodField()
    lastName = serializers.SerializerMethodField()
    telephone = serializers.SerializerMethodField()
    adresse = serializers.SerializerMethodField()
    dateInscription = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    totalCommandes = serializers.SerializerMethodField()
    montantTotal = serializers.SerializerMethodField()
    derniereCommande = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'phone', 'address', 'is_verified', 
                'firstName', 'lastName', 'role', 'is_staff', 'is_superuser',
                'telephone', 'adresse', 'dateInscription', 'type', 
                'totalCommandes', 'montantTotal', 'derniereCommande')
        read_only_fields = ('id', 'is_verified', 'is_staff', 'is_superuser')
    


    def get_telephone(self, obj):
        return obj.phone

    def get_adresse(self, obj):
        return obj.address

    def get_dateInscription(self, obj):
        return obj.created_at.strftime('%d/%m/%Y') if obj.created_at else ""

    def get_type(self, obj):
        # You can determine this based on business logic
        # For now, default to "particulier"
        return "particulier"  # or implement your logic

    def get_totalCommandes(self, obj):
        # Count orders for this user
        return obj.user_orders.count() if hasattr(obj, 'user_orders') else 0

    def get_montantTotal(self, obj):
        # Sum total amount from user's orders
        if hasattr(obj, 'user_orders'):
            return sum(order.total_amount for order in obj.user_orders.all())
        return 0

    def get_derniereCommande(self, obj):
        # Get last order date
        if hasattr(obj, 'user_orders'):
            last_order = obj.user_orders.order_by('-created_at').first()
            return last_order.created_at.strftime('%d/%m/%Y') if last_order else "Aucune"
        return "Aucune"
    # def get_role(self, obj):
    #     """Return the role directly from the model"""
    #     return obj.role
        
    def get_firstName(self, obj):
        """Extract first name from username or email"""
        if hasattr(obj, 'first_name') and obj.first_name:
            return obj.first_name
        # Fallback: extract from username
        if '_' in obj.username:
            return obj.username.split('_')[0].title()
        return obj.username.title()
        
    def get_lastName(self, obj):
        """Extract last name from username or email"""
        if hasattr(obj, 'last_name') and obj.last_name:
            return obj.last_name
        # Fallback: extract from username
        if '_' in obj.username:
            parts = obj.username.split('_')
            return parts[-1].title() if len(parts) > 1 else ""
        return ""

    # def get_role(self, obj):
    #     if obj.is_staff or obj.is_superuser:
    #         return "admin"
    #     return "customer"
    def get_role(self, obj):
        if obj.is_superuser or obj.is_staff:
            return "admin"
        elif obj.role == "sales":
            return "sales"
        elif obj.role == "purchasing":
            return "purchasing"
        else:
            return "customer"
