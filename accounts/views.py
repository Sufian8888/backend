from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
import random
import string
from .permanent_permissions import IsAdmin

from .models import CustomUser
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from .email_utils import send_welcome_email, send_password_reset_email
# from django.core.mail import send_mail
# from django.conf import settings

# def index(request):
#     if request.method == 'POST':
#         message = request.POST['This is testing email for SMTP Verification for registeration fro pneushop.tn']
#         email = request.POST['zmarketingcompany@gmail.com']
#         name = request.POST['Muhammad Sufian']
#         send_mail(
#             'Registeration Testing',
#             message,
#             'settings.EMAIL_HOST_USER',
#             [email],
#             fail_silently=False,

#         )
    
#     return Response(request)

from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse

def index(request):
    if request.method == 'GET':  # trigger email on GET for testing
        send_mail(
            subject='Registration Testing',
            message='This is a testing email for SMTP verification.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['zmarketingcompany@gmail.com'],  # hardcoded test recipient
            fail_silently=False,
        )
        return HttpResponse("Test email sent!")

    return HttpResponse("Go to /?test=1 to trigger test email.")
 

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        user.verification_code = verification_code
        user.save()
        
        # Send welcome email with verification
        try:
            send_welcome_email(user)
            print(f"Welcome email sent to {user.email}")
        except Exception as e:
            print(f"Erreur envoi email de bienvenue: {e}")
        
        # Send verification email
        try:
            send_mail(
                'Vérification de votre compte PneuShop',
                f'Votre code de vérification est: {verification_code}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
            print(f"Verification email sent to {user.email}")
        except Exception as e:
            print(f"Erreur envoi email de vérification: {e}")
        
        return Response({
            'success': True,
            'message': 'Compte créé avec succès. Vérifiez votre email.',
            'user_id': user.id,
            'user': UserSerializer(user).data  # Add user data

        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    
    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': UserSerializer(user).data
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    user_id = request.data.get('user_id')
    code = request.data.get('code')
    
    try:
        user = CustomUser.objects.get(id=user_id)
        if user.verification_code == code:
            user.is_verified = True
            user.verification_code = ''
            user.save()
            return Response({'message': 'Email vérifié avec succès.'})
        else:
            return Response({'error': 'Code de vérification incorrect.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
    except CustomUser.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé.'}, 
                      status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email')
    try:
        user = CustomUser.objects.get(email=email)
        
        # Generate secure token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create reset URL
        reset_url = f"http://localhost:3000/auth/reset-password?uid={uid}&token={token}"
        
        # Get client IP for security
        request_ip = request.META.get('HTTP_X_FORWARDED_FOR', 
                                    request.META.get('REMOTE_ADDR', 'Unknown'))
        
        # Send password reset email
        try:
            send_password_reset_email(user, reset_url, token, request_ip)
            print(f"Password reset email sent to {user.email}")
        except Exception as e:
            print(f"Erreur envoi email de réinitialisation: {e}")
        
        return Response({
            'message': 'Instructions de réinitialisation envoyées par email.',
            'uid': uid,  # For development/testing
            'token': token  # For development/testing
        })
    except CustomUser.DoesNotExist:
        return Response({'error': 'Email non trouvé.'}, 
                      status=status.HTTP_404_NOT_FOUND)

# @api_view(['GET'])
# def user_profile(request):
#     """Get current user profile information"""
#     serializer = UserSerializer(request.user)
#     return Response(serializer.data)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])  # Add this line to ensure only authenticated users can access
def user_profile(request):
    """Get or update current user profile information"""
    user = request.user
    
    if request.method == 'PATCH':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            # Handle first_name and last_name from the request
            if 'firstName' in request.data:
                user.first_name = request.data['firstName']
            if 'lastName' in request.data:
                user.last_name = request.data['lastName']
            if 'phone' in request.data:
                user.phone = request.data['phone']
            if 'address' in request.data:
                user.address = request.data['address']
            if 'email' in request.data:
                user.email = request.data['email']
            user.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # GET request handling remains the same
    serializer = UserSerializer(user)
    return Response(serializer.data)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password with secure token"""
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    try:
        # Decode user ID
        user_id = urlsafe_base64_decode(uid).decode()
        user = CustomUser.objects.get(pk=user_id)
        
        # Verify token
        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Mot de passe réinitialisé avec succès.'})
        else:
            return Response({'error': 'Token invalide ou expiré.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, CustomUser.DoesNotExist):
        return Response({'error': 'Lien de réinitialisation invalide.'}, 
                      status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_token(request):
    """Verify if reset token is valid"""
    uid = request.data.get('uid')
    token = request.data.get('token')
    
    try:
        user_id = urlsafe_base64_decode(uid).decode()
        user = CustomUser.objects.get(pk=user_id)
        
        if default_token_generator.check_token(user, token):
            return Response({
                'valid': True,
                'email': user.email,
                'message': 'Token valide'
            })
        else:
            return Response({
                'valid': False,
                'message': 'Token invalide ou expiré'
            }, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, CustomUser.DoesNotExist):
        return Response({
            'valid': False,
            'message': 'Token invalide'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # only logged-in users
def clients_list(request):
    # Only non-admin users
    clients = CustomUser.objects.filter(is_staff=False, is_superuser=False)
    serializer = UserSerializer(clients, many=True)
    return Response(serializer.data)



# @api_view(['POST'])
# @permission_classes([IsAdmin])
# def create_user(request):
#     data = request.data
#     user = CustomUser.objects.create_user(
#         username=data["email"],
#         email=data["email"],
#         first_name=data["firstName"],
#         last_name=data["lastName"],
#         password=data["password"],
#         role=data["role"],  # "sales" or "purchasing"
#     )
#     serializer = UserSerializer(user)
#     return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_staff_users(request):
    """
    List all non-customer users with optional role filtering
    Query params:
    - role: Optional filter by role (purchasing, sales, or admin)
    """
    # Check if user is admin or superuser
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return Response(
            {'error': 'You do not have permission to view this resource'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get role filter from query params
    role = request.query_params.get('role')
    
    # Base query for all non-customer users
    users = CustomUser.objects.exclude(role='customer')
    
    # Apply role filter if provided
    if role and role in ['purchasing', 'sales', 'admin']:
        users = users.filter(role=role)
    
    # Debug: Print the query and results
    print(f"Query: {users.query}")
    print(f"Found {users.count()} users with role: {role or 'all'}")
    
    # Serialize and return the results
    serializer = UserSerializer(users, many=True)
    return Response({
        'count': users.count(),
        'users': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user(request):
    # Check if user is either admin or superuser
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return Response(
            {'error': 'You do not have permission to perform this action'},
            status=status.HTTP_403_FORBIDDEN
        )
    # Only allow creating purchasing and sales accounts
    role = request.data.get('role')
    if role not in ['purchasing', 'sales']:
        return Response(
            {'error': 'You can only create purchasing or sales accounts'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set is_verified to True for staff accounts
    data = request.data.copy()
    data['is_verified'] = True
    
    # Create a copy of the data and ensure role is set
    user_data = data.copy()
    user_data['role'] = role  # Ensure role is set from the validated request
    
    serializer = UserRegistrationSerializer(data=user_data)
    if serializer.is_valid():
        user = serializer.save()
        # Send welcome email with credentials
        try:
            send_welcome_email(user)
        except Exception as e:
            print(f"Error sending welcome email: {e}")
            
        # Return the created user data with the role from the serializer
        response_data = {
            'message': f'{role.capitalize()} account created successfully',
            'user': {
                **UserSerializer(user).data,
                'role': role  # Explicitly set the role in the response
            }
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    # Check if user has permission (admin or superuser)
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return Response(
            {'error': 'You do not have permission to perform this action'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Prevent modifying superuser accounts unless current user is superuser
    if user.is_superuser and not request.user.is_superuser:
        return Response(
            {'error': 'Cannot modify superuser account'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Don't allow changing role to/from superuser
    data = request.data.copy()
    if 'is_superuser' in data:
        data.pop('is_superuser')
    
    # Only allow updating specific fields
    allowed_fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'role', 'is_active']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    # Update user
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Handle password separately
    if 'password' in data:
        user.set_password(data['password'])
    
    user.save()
    
    return Response({
        'message': 'User updated successfully',
        'user': UserSerializer(user).data
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    # Check if user has permission (admin or superuser)
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return Response(
            {'error': 'You do not have permission to perform this action'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Prevent deleting own account or superuser accounts
    if user == request.user:
        return Response(
            {'error': 'You cannot delete your own account'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if user.is_superuser and not request.user.is_superuser:
        return Response(
            {'error': 'Cannot delete superuser account'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user.delete()
    return Response(
        {'message': 'User deleted successfully'},
        status=status.HTTP_204_NO_CONTENT
    )