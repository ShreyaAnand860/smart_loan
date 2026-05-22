from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import CreditScore, Document, EMIRecord, LoanApplication, LoanType, Notification, Payment

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "phone", "address", "pan_number", "aadhaar_number", "role", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data["role"] = User.Role.CUSTOMER
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoanTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanType
        fields = "__all__"


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = ["status", "remarks", "uploaded_at"]


class LoanApplicationSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    loan_type_name = serializers.CharField(source="loan_type.name", read_only=True)

    class Meta:
        model = LoanApplication
        fields = "__all__"
        read_only_fields = [
            "applicant",
            "status",
            "prediction_label",
            "approval_probability",
            "risk_score",
            "risk_level",
            "rejection_reason",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class EMIRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMIRecord
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["status", "transaction_reference", "paid_at", "created_at"]


class CreditScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditScore
        fields = "__all__"
        read_only_fields = ["user", "checked_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ["user", "created_at"]