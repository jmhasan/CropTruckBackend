from rest_framework import serializers

from inventory.models import Stock, Imtrn, Imtor


class CurrentStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'


class ImtorSerializer(serializers.ModelSerializer):
    class Meta:
        model= Imtor
        exclude = ['pk']
        read_only_fields = ['business_id', 'booking_no', 'updated_by', 'created_at', 'updated_at','xtype']