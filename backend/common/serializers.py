from rest_framework import serializers
from datetime import datetime
from django.utils.translation import gettext as _
from .models import User, Book, BookRequest, Address, PickupPoint
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    street = serializers.CharField(write_only=True)
    number = serializers.CharField(write_only=True)
    city = serializers.CharField(write_only=True)
    zip = serializers.CharField(write_only=True)
    address = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'birth_date', 'phone', 'street', 'number', 'city', 'zip', 'address']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_address(self, obj):
        address = Address.objects.filter(user=obj).first()
        if address:
            return {
                'street': address.street,
                'number': address.number,
                'city': address.city,
                'zip': address.zip,
            }
        return None

    # Validação da senha - pelo menos 6 caracteres
    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError(_("A senha deve ter pelo menos 6 caracteres."))
        return value

    # Validação da data de nascimento - mês e dia entre limites e ano não pode ser futuro
    def validate_birth_date(self, value):
        today = datetime.today()
        if value.year > today.year:
            raise serializers.ValidationError(_("Insira uma data de nascimento válida."))

        age = today.year - value.year
        if today.month < value.month or (today.month == value.month and today.day < value.day):
            age -= 1

        if age < 18:
            raise serializers.ValidationError(_("O usuário precisa ter pelo menos 18 anos."))
        if age > 120:
            raise serializers.ValidationError(_("A data de nascimento não pode indicar mais de 120 anos de idade."))
    
        return value

    # Validação do telefone - deve conter 11 dígitos
    def validate_phone(self, value):
        if len(value) not in [10, 11] or not value.isdigit():
            raise serializers.ValidationError("O número de telefone deve conter entre 10 a 11 dígitos (somente números).")
        if not value.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
            raise serializers.ValidationError("O número de telefone deve começar com um DDD válido.")
        return value

    def validate_street(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("O campo rua não pode estar vazio."))
        return value

    def validate_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(_("O campo número deve conter apenas números."))
        return value

    def validate_city(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("O campo cidade não pode estar vazio."))
        return value

    def validate_zip(self, value):
        if not value.isdigit() or len(value) != 8:
            raise serializers.ValidationError(_("O campo cep deve conter exatamente 8 dígitos numéricos."))
        return value

    def create(self, validated_data):
        street = validated_data.pop('street')
        number = validated_data.pop('number')
        city = validated_data.pop('city')
        zip_code = validated_data.pop('zip')

        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()

        Address.objects.create(
            user=user,
            street=street,
            number=number,
            city=city,
            zip=zip_code
        )

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        address_data = {
            'street': validated_data.get('street'),
            'number': validated_data.get('number'),
            'city': validated_data.get('city'),
            'zip': validated_data.get('zip'),
        }

        if any(address_data.values()):
            self.update_address(instance, address_data)

        return instance

    def update_address(self, instance, address_data):
        address, _ = Address.objects.get_or_create(user=instance)
        for attr, value in address_data.items():
            if value is not None:
                setattr(address, attr, value)
        address.save()

#Ponto de Coleta
class PickupPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupPoint
        fields = '__all__'

#Solicitação de Livro
class BookDonorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email']

class BookInfoSerializer(serializers.ModelSerializer):
    donated_by = BookDonorSerializer(source='user', read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'donated_by']

class BookRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='user.name', read_only=True)
    book = BookInfoSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), write_only=True)
    pickup_point = PickupPointSerializer(source='book.pickup_point', read_only=True)

    class Meta:
        model = BookRequest
        fields = ['id', 'book', 'book_id', 'requester_name', 'pickup_point', 'status']
        read_only_fields = ['user', 'id', 'book', 'requester_name', 'status']

    def create(self, validated_data):
        validated_data['book'] = validated_data.pop('book_id')
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop('book_id', None)
        return rep

class SimplifiedBookRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = BookRequest
        fields = ['id', 'requester_name', 'status']

#Livros
class BookSerializer(serializers.ModelSerializer):
    pickup_point = PickupPointSerializer(read_only=True)
    pickup_point_id = serializers.PrimaryKeyRelatedField(
        queryset=PickupPoint.objects.all(), source='pickup_point', write_only=True
    )
    user = serializers.StringRelatedField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)  # Adiciona o ID do proprietário
    user_email = serializers.EmailField(source='user.email', read_only=True)  # Adiciona o email do proprietário
    book_request = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'description', 'category', 'classification',
            'pickup_point', 'pickup_point_id', 'status', 'user', 'user_id', 'user_email', 'book_request'
        ]

    def get_book_request(self, obj):
        # Retorna informações da solicitação associada, se houver
        book_request = obj.book_request
        if book_request:
            return {
                'id': book_request.id,
                'requester_name': book_request.user.name,
                'status': book_request.status
            }
        return None
