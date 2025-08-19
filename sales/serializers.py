from rest_framework import serializers
from .models import SalesData

class SalesDataSerializer(serializers.ModelSerializer):
    profit = serializers.FloatField(read_only=True)

    class Meta:
        model = SalesData
        fields = '__all__'
