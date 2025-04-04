from rest_framework import serializers
from datetime import datetime
from .models import User, Book, BookRequest

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'birth_date', 'phone']
        extra_kwargs = {
            'password': {'write_only': True},  # Não enviar a senha em respostas
        }

    # Validação da senha - pelo menos 6 caracteres
    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("A senha deve ter pelo menos 6 caracteres.")
        return value

    # Validação da data de nascimento - mês e dia entre limites e ano não pode ser futuro
    def validate_birth_date(self, value):
        today = datetime.today()
        if value.year > today.year:
            raise serializers.ValidationError("Insira a data corretamente")
    
    # Verificando se a pessoa tem pelo menos 18 anos
        age = today.year - value.year
        if today.month < value.month or (today.month == value.month and today.day < value.day):
            age -= 1

        if age < 18:
            raise serializers.ValidationError("O usuário precisa ter pelo menos 18 anos.")
    
        return value

    # Validação do telefone - deve conter 11 dígitos
    def validate_phone(self, value):
        if len(value) not in [10, 11] or not value.isdigit():
            raise serializers.ValidationError("O número de telefone deve conter entre 10 a 11 dígitos (somente números).")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

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

    def create(self, validated_data):
        # Atribuindo automaticamente o 'user' durante a criação
        validated_data['book'] = validated_data.pop('book_id')
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)



#Books


class BookSerializer(serializers.ModelSerializer):
    book_request = BookRequestSerializer(read_only=True)  # Exibindo a solicitação associada ao livro
    user = serializers.StringRelatedField()  # Exibindo o nome do usuário associado ao livro

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'description', 'category', 'classification', 'status', 'user', 'book_request']
        read_only_fields = ['user', 'created_at']
        