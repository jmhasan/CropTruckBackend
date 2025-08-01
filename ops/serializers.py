from django.core.validators import RegexValidator
from rest_framework import serializers

from masterdata.models import CustomerProfile
from ops.models import TokenNumber, Booking, Certificate


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenNumber
        # fields = '__all__'
        exclude = ['pk']
        read_only_fields = ['token_no', 'created_by', 'updated_by', 'created_at', 'updated_at']


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        # fields = '__all__'
        exclude = ['pk']
        read_only_fields = ['business_id', 'booking_no', 'updated_by', 'created_at', 'updated_at']


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            'customer_code',
            'customer_name',
            'contact_person',
            'xphone',
            'xmobile',
            'xemail',
            'xwebsite',
            'father_name',
            'division_name',
            'district_name',
            'upazila_name',
            'union_name',
            'village',
            'post_office',
            'postal_code',
            'xaddress',
            'trade_license_number',
            'bin_number',
            'tin_number',
            'credit_limit',
            'credit_terms_days',
            'default_discount',
            'customer_type',
            'group_name',
            'is_active',
            'remarks',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['customer_code', 'created_at', 'updated_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'booking_no',
            'customer_code',
            'xmobile',
            'xname',
            'father_name',
            'district_name',
            'division_name',
            'upazila_name',
            'union_name',
            'village',
            'post_office',
            'xadvance',
            'xsack'
        ]
        extra_kwargs = {
            'booking_no': {'required': False},
            'customer_code': {'required': False},
            'xmobile': {
                'required': True,
                'validators': [
                    RegexValidator(
                        regex=r'^01[3-9]\d{8}$',
                        message='Enter a valid Bangladeshi mobile number (e.g. 017XXXXXXXX).'
                    )
                ]
            },
            'xname': {'required': True, 'max_length': 150},
            'father_name': {'required': False, 'allow_blank': True},
            'district_name': {'required': False, 'allow_blank': True},
            'division_name': {'required': False, 'allow_blank': True},
            'upazila_name': {'required': False, 'allow_blank': True},
            'union_name': {'required': False, 'allow_blank': True},
            'village': {'required': False, 'allow_blank': True},
            'post_office': {'required': False, 'allow_blank': True},
            'xadvance': {'required': False, 'min_value': 0},
            'xsack': {'required': False, 'min_value': 0}
        }

    def validate(self, attrs):
        """
        Custom validation for composite primary key
        """
        request = self.context.get('request')
        booking_no = attrs.get('booking_no')

        if booking_no and request and hasattr(request.user, 'business_id'):
            existing_booking = Booking.objects.filter(
                business_id=request.user.business_id,
                booking_no=booking_no
            ).exists()
            if existing_booking:
                raise serializers.ValidationError({
                    'booking_no': 'A booking with this booking number already exists for this business.'
                })

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        business = validated_data.pop('business_id')
        mobile_number = validated_data.get('xmobile')

        # Try to find existing customer by mobile number
        existing_customer = CustomerProfile.objects.filter(
            business_id=business,
            xmobile=mobile_number
        ).first()

        if existing_customer:
            # Customer exists - use existing customer data and update customer_code in booking
            validated_data['customer_code'] = existing_customer.customer_code

            # Optionally update customer profile with new booking information if provided
            update_fields = []
            if validated_data.get('xname') and validated_data['xname'] != existing_customer.customer_name:
                existing_customer.customer_name = validated_data['xname']
                update_fields.append('customer_name')

            if validated_data.get('father_name') and validated_data['father_name'] != existing_customer.father_name:
                existing_customer.father_name = validated_data['father_name']
                update_fields.append('father_name')

            if validated_data.get('district_name') and validated_data[
                'district_name'] != existing_customer.district_name:
                existing_customer.district_name = validated_data['district_name']
                update_fields.append('district_name')

            if validated_data.get('division_name') and validated_data[
                'division_name'] != existing_customer.division_name:
                existing_customer.division_name = validated_data['division_name']
                update_fields.append('division_name')

            if validated_data.get('upazila_name') and validated_data['upazila_name'] != existing_customer.upazila_name:
                existing_customer.upazila_name = validated_data['upazila_name']
                update_fields.append('upazila_name')

            if validated_data.get('union_name') and validated_data['union_name'] != existing_customer.union_name:
                existing_customer.union_name = validated_data['union_name']
                update_fields.append('union_name')

            if validated_data.get('village') and validated_data['village'] != existing_customer.village:
                existing_customer.village = validated_data['village']
                update_fields.append('village')

            if validated_data.get('post_office') and validated_data['post_office'] != existing_customer.post_office:
                existing_customer.post_office = validated_data['post_office']
                update_fields.append('post_office')

            # Save customer if any updates were made
            if update_fields:
                existing_customer.updated_by = request.user if request else None
                existing_customer.save(update_fields=update_fields + ['updated_by', 'updated_at'])
        else:
            # Customer doesn't exist - create new customer profile
            customer_data = {
                'business_id': business,
                'customer_name': validated_data.get('xname'),
                'xmobile': mobile_number,
                'father_name': validated_data.get('father_name', ''),
                'district_name': validated_data.get('district_name', ''),
                'division_name': validated_data.get('division_name', ''),
                'upazila_name': validated_data.get('upazila_name', ''),
                'union_name': validated_data.get('union_name', ''),
                'village': validated_data.get('village', ''),
                'post_office': validated_data.get('post_office', ''),
                'customer_type': 'Farmer',  # Default type
                'is_active': True,
                'created_by': request.user if request else None
            }

            new_customer = CustomerProfile.objects.create(**customer_data)
            validated_data['customer_code'] = new_customer.customer_code

        # Add audit fields to validated_data
        if request and request.user:
            validated_data['created_by'] = request.user
            validated_data['updated_by'] = request.user

        # Create booking
        booking = Booking.objects.create(
            business_id=business,
            **validated_data
        )

        return booking

class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'
        read_only_fields = ['business_id', 'zactive']