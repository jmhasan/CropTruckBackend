from rest_framework import serializers
from rest_framework import serializers
from .models import CustomerProfile, GeoLocation, CompanyProfile, RateSetup
from masterdata.models import CommonCodes, GeoLocation

class CommonCodesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonCodes
        fields = ['xtype', 'xcode']
        read_only_fields = ['business_id', 'zactive']

class GeoLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLocation
        exclude = ['pk']

class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLocation
        fields = ['division_name', 'division_bn']

    def to_representation(self, instance):
        return {
            'division_name': instance.division_name,
            'division_bn': instance.division_bn
        }


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLocation
        fields = ['division_name', 'division_bn', 'district_name', 'district_bn']

    def to_representation(self, instance):
        return {
            'division_name': instance.division_name,
            'division_bn': instance.division_bn,
            'district_name': instance.district_name,
            'district_bn': instance.district_bn
        }


class UpazilaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLocation
        fields = ['division_name', 'division_bn', 'district_name', 'district_bn',
                  'upazila_name', 'upazila_bn']

    def to_representation(self, instance):
        return {
            'division_name': instance.division_name,
            'division_bn': instance.division_bn,
            'district_name': instance.district_name,
            'district_bn': instance.district_bn,
            'upazila_name': instance.upazila_name,
            'upazila_bn': instance.upazila_bn
        }


class UnionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLocation
        fields = ['division_name', 'division_bn', 'district_name', 'district_bn',
                  'upazila_name', 'upazila_bn', 'union_name', 'union_bn']


class CustomerProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating customer profile with geo-location validation"""

    # Make some fields required for creation
    customer_name = serializers.CharField(max_length=255, required=True)
    xmobile = serializers.CharField(max_length=20, required=True)
    customer_type = serializers.ChoiceField(
        choices=[
            ('Farmer', 'Farmer'),
            ('Retailer', 'Retailer'),
            ('Dealer', 'Dealer'),
            ('Corporate', 'Corporate'),
            ('Trader', 'Trader'),
            ('Agent', 'Agent'),
        ],
        default='Farmer'
    )

    # Geo-location fields validation
    division_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    district_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    upazila_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    union_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

    class Meta:
        model = CustomerProfile
        fields = [
            'customer_name', 'contact_person',
            'xphone', 'xmobile', 'xemail', 'xwebsite',
            'father_name',
            'division_name', 'district_name', 'upazila_name', 'union_name',
            'village', 'post_office', 'postal_code', 'xaddress',
            'trade_license_number', 'bin_number', 'tin_number',
            'credit_limit', 'credit_terms_days', 'default_discount',
            'customer_type', 'group_name', 'is_active', 'remarks'
        ]
        extra_kwargs = {
            'customer_name': {'required': True},
            'xmobile': {'required': True},
            'xemail': {'required': False},
        }

    def validate_xmobile(self, value):
        """Validate mobile number format and uniqueness"""
        if not value:
            raise serializers.ValidationError("Mobile number is required")

        # Basic mobile number validation (adjust pattern as needed)
        import re
        if not re.match(r'^(\+88)?01[3-9]\d{8}$', value):
            raise serializers.ValidationError("Invalid mobile number format")

        return value

    def validate_xemail(self, value):
        """Validate email format"""
        if value and value.strip():
            # Additional email validation if needed
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise serializers.ValidationError("Invalid email format")
        return value

    def validate_geo_location(self, attrs):
        """Validate geo-location hierarchy"""
        division = attrs.get('division_name')
        district = attrs.get('district_name')
        upazila = attrs.get('upazila_name')
        union = attrs.get('union_name')

        # If any geo field is provided, validate the hierarchy
        if any([division, district, upazila, union]):
            business_id = self.context['request'].user.business_id

            # Check if the geo-location combination exists
            geo_query = GeoLocation.objects.filter(business_id=business_id)

            if division:
                geo_query = geo_query.filter(division_name=division)
            if district:
                if not division:
                    raise serializers.ValidationError({
                        'district_name': 'Division must be provided when district is specified'
                    })
                geo_query = geo_query.filter(district_name=district)
            if upazila:
                if not district or not division:
                    raise serializers.ValidationError({
                        'upazila_name': 'Division and district must be provided when upazila is specified'
                    })
                geo_query = geo_query.filter(upazila_name=upazila)
            if union:
                if not upazila or not district or not division:
                    raise serializers.ValidationError({
                        'union_name': 'Division, district, and upazila must be provided when union is specified'
                    })
                geo_query = geo_query.filter(union_name=union)

            if not geo_query.exists():
                raise serializers.ValidationError({
                    'geo_location': 'Invalid geo-location combination'
                })

        return attrs

    def validate(self, attrs):
        """Overall validation"""
        # Validate geo-location
        attrs = self.validate_geo_location(attrs)

        # Check for duplicate customer (business_id + customer_code + xmobile)
        business_id = self.context['request'].user.business_id
        xmobile = attrs.get('xmobile')

        if CustomerProfile.objects.filter(
                business_id=business_id,
                xmobile=xmobile
        ).exists():
            raise serializers.ValidationError({
                'xmobile': 'A customer with this mobile number already exists'
            })

        return attrs


class CustomerProfileResponseSerializer(serializers.ModelSerializer):
    """Serializer for response data"""
    business_name = serializers.CharField(source='business_id.company_name', read_only=True)

    class Meta:
        model = CustomerProfile
        exclude = ['pk']
        read_only_fields = ['business_id', 'customer_code']


class CustomerProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating customer profile with geo-location validation"""

    # Optional fields for update
    customer_name = serializers.CharField(max_length=255, required=False)
    xmobile = serializers.CharField(max_length=20, required=False)
    customer_type = serializers.ChoiceField(
        choices=[
            ('Farmer', 'Farmer'),
            ('Retailer', 'Retailer'),
            ('Dealer', 'Dealer'),
            ('Corporate', 'Corporate'),
            ('Trader', 'Trader'),
            ('Agent', 'Agent'),
        ],
        required=False
    )

    # Geo-location fields validation
    division_name = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    district_name = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    upazila_name = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    union_name = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = CustomerProfile
        fields = [
            'customer_name', 'contact_person',
            'xphone', 'xmobile', 'xemail', 'xwebsite',
            'father_name',
            'division_name', 'district_name', 'upazila_name', 'union_name',
            'village', 'post_office', 'postal_code', 'xaddress',
            'trade_license_number', 'bin_number', 'tin_number',
            'credit_limit', 'credit_terms_days', 'default_discount',
            'customer_type', 'group_name', 'is_active', 'remarks'
        ]
        extra_kwargs = {
            'customer_name': {'required': False},
            'xmobile': {'required': False},
            'xemail': {'required': False},
        }

    def validate_xmobile(self, value):
        """Validate mobile number format and uniqueness (excluding current instance)"""
        if value and value.strip():
            # Basic mobile number validation
            import re
            if not re.match(r'^(\+88)?01[3-9]\d{8}$', value):
                raise serializers.ValidationError("Invalid mobile number format")

        return value

    def validate_xemail(self, value):
        """Validate email format"""
        if value and value.strip():
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise serializers.ValidationError("Invalid email format")
        return value

    def validate_geo_location(self, attrs):
        """Validate geo-location hierarchy"""
        division = attrs.get('division_name')
        district = attrs.get('district_name')
        upazila = attrs.get('upazila_name')
        union = attrs.get('union_name')

        # If any geo field is provided, validate the hierarchy
        if any([division, district, upazila, union]):
            business_id = self.context['request'].user.business_id

            # Check if the geo-location combination exists
            geo_query = GeoLocation.objects.filter(business_id=business_id)

            if division:
                geo_query = geo_query.filter(division_name=division)
            if district:
                if not division:
                    raise serializers.ValidationError({
                        'district_name': 'Division must be provided when district is specified'
                    })
                geo_query = geo_query.filter(district_name=district)
            if upazila:
                if not district or not division:
                    raise serializers.ValidationError({
                        'upazila_name': 'Division and district must be provided when upazila is specified'
                    })
                geo_query = geo_query.filter(upazila_name=upazila)
            if union:
                if not upazila or not district or not division:
                    raise serializers.ValidationError({
                        'union_name': 'Division, district, and upazila must be provided when union is specified'
                    })
                geo_query = geo_query.filter(union_name=union)

            if not geo_query.exists():
                raise serializers.ValidationError({
                    'geo_location': 'Invalid geo-location combination'
                })

        return attrs

    def validate(self, attrs):
        """Overall validation for update"""
        # Validate geo-location
        attrs = self.validate_geo_location(attrs)

        # Check for duplicate mobile number (excluding current instance)
        xmobile = attrs.get('xmobile')
        if xmobile and self.instance:
            business_id = self.context['request'].user.business_id

            # Check if another customer has this mobile number
            duplicate_check = CustomerProfile.objects.filter(
                business_id=business_id,
                xmobile=xmobile
            ).exclude(
                business_id=self.instance.business_id,
                customer_code=self.instance.customer_code
            )

            if duplicate_check.exists():
                raise serializers.ValidationError({
                    'xmobile': 'Another customer with this mobile number already exists'
                })

        return attrs


class RateSetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateSetup
        fields = ['xyear', 'xtype', 'xrate']