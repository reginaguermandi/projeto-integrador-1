from rest_framework import serializers
from datetime import datetime
from django.utils.translation import gettext as _
from .models import User, Book, BookRequest, Address

class UserSerializer(serializers.ModelSerializer):
    street = serializers.CharField(write_only=True)
    number = serializers.CharField(write_only=True)
    city = serializers.CharField(write_only=True)
    zip = serializers.CharField(write_only=True)

    # Adicionando campos de endereço na resposta
    address = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'birth_date', 'phone', 'street', 'number', 'city', 'zip', 'address']
        extra_kwargs = {
            'password': {'write_only': True},  # Não enviar a senha em respostas
        }

    def get_address(self, obj):
        # Recupera o endereço associado ao usuário
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
            raise serializers.ValidationError(_("O campo 'street' não pode estar vazio."))
        return value

    def validate_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(_("O campo 'number' deve conter apenas números."))
        return value

    def validate_city(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("O campo 'city' não pode estar vazio."))
        return value

    def validate_zip(self, value):
        if not value.isdigit() or len(value) != 8:
            raise serializers.ValidationError(_("O campo 'zip' deve conter exatamente 8 dígitos numéricos."))
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

#Book Request
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
    book = BookInfoSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), write_only=True)

    class Meta:
        model = BookRequest
        fields = ['id', 'book', 'book_id', 'delivery_option', 'status']
        read_only_fields = ['user']

    def validate(self, data):
        book = data['book_id']
        user = self.context['request'].user

        # Verificar se o usuário está tentando solicitar seu próprio livro
        if book.user == user:
            raise serializers.ValidationError(_("Você não pode solicitar um livro que você mesmo cadastrou."))

        # Verificar se já existe uma solicitação pendente para o livro
        if BookRequest.objects.filter(book=book, status='pending').exists():
            raise serializers.ValidationError(_("Este livro já tem um pedido pendente."))

        # Verificar se o livro está disponível
        if book.status != 'available':
            raise serializers.ValidationError(_("Este livro não está disponível para doação."))

        return data

    def create(self, validated_data):
        # Atribuir automaticamente o 'user' durante a criação
        validated_data['book'] = validated_data.pop('book_id')
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Remove o book_id da resposta (só serve pro POST)
        rep.pop('book_id', None)
        return rep



#Books


class BookSerializer(serializers.ModelSerializer):
    book_request = BookRequestSerializer(read_only=True)  # Exibindo a solicitação associada ao livro
    user = serializers.StringRelatedField()  # Exibindo o nome do usuário associado ao livro

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'description', 'category', 'classification', 'status', 'user', 'book_request']
        read_only_fields = ['user', 'created_at']
