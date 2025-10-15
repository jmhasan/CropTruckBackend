from rest_framework import serializers

from accounts.models import Glmst, Glsub


class ChartofAccountsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Glmst
        # exclude = ['business_id']
        fields = '__all__'
        read_only_fields = ['business_id','xteam','xmember','xmanager','created_by','updated_by','created_at','updated_at']


class SubAccountSerializer(serializers.ModelSerializer):
    # This field handles the composite primary key for read operations
    pk = serializers.ReadOnlyField()

    class Meta:
        model = Glsub
        fields = '__all__'
        read_only_fields = ['business_id','created_by', 'updated_by', 'created_at', 'updated_at']
