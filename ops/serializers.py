from django.core.validators import RegexValidator
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from masterdata.models import CustomerProfile, ItemMaster, CompanyProfile
from ops.models import TokenNumber, Booking, Certificate, CertificateDetails


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
        # fields = '__all__'
        exclude = ['pk']
        read_only_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')


class CertificateCreateSerializer(serializers.Serializer):
    # Required fields (business_id will be handled from user profile)
    token_no = serializers.CharField(max_length=10)
    xmobile = serializers.CharField(max_length=20)  # Mandatory
    customer_name = serializers.CharField(max_length=255)
    number_of_sacks = serializers.IntegerField()
    number_of_empty_sacks = serializers.IntegerField()

    # Optional certificate fields
    certificate_no = serializers.CharField(max_length=20, required=False, allow_blank=True)
    booking_no = serializers.CharField(max_length=50, required=False, allow_blank=True)

    # Customer contact information
    contact_person = serializers.CharField(max_length=100, required=False, allow_blank=True)
    xphone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    xemail = serializers.EmailField(required=False, allow_blank=True)

    # Customer address fields
    father_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    division_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    district_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    upazila_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    union_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    village = serializers.CharField(max_length=100, required=False, allow_blank=True)
    post_office = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    xaddress = serializers.CharField(max_length=255, required=False, allow_blank=True)

    # Customer classification
    customer_type = serializers.ChoiceField(
        choices=[
            ('Farmer', 'Farmer'),
            ('Retailer', 'Retailer'),
            ('Dealer', 'Dealer'),
            ('Corporate', 'Corporate'),
            ('Trader', 'Trader'),
            ('Agent', 'Agent'),
        ],
        default='Farmer',
        required=False
    )

    # Business/Legal Details
    trade_license_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    bin_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tin_number = serializers.CharField(max_length=100, required=False, allow_blank=True)

    # Financial Details
    credit_limit = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    credit_terms_days = serializers.IntegerField(required=False)
    default_discount = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)

    # Additional fields
    group_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)

    # Business fields
    potato_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    rent_per_sack = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_rent = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    advance_rent = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    remaining_rent = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    price_of_empty_sacks = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    transportation = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    given_loan = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    total_amount_taka = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)

    def validate_xmobile(self, value):
        """Validate mobile number format"""
        if not value:
            raise serializers.ValidationError("Mobile number is mandatory for certificate creation.")

        # Add your mobile number validation logic here
        if len(value) < 10:
            raise serializers.ValidationError("Mobile number must be at least 10 digits.")

        return value

    def validate_token_no(self, value):
        """Validate token format"""
        if not value:
            raise serializers.ValidationError("Token number is required.")
        return value


# class CertificateDetailsBulkCreateSerializer(serializers.Serializer):
#     """Serializer for bulk creating certificate details"""
#
#     # Individual detail serializer
#     class CertificateDetailItemSerializer(serializers.ModelSerializer):
#         class Meta:
#             model = CertificateDetails
#             fields = [
#                 'business_id',
#                 'certificate_no',
#                 'xitem',
#                 'xunit',
#                 'xfloor',
#                 'xpocket',
#                 'potato_type',
#                 'number_of_sacks',
#                 'rent_per_sack'
#             ]
#
#         def validate_number_of_sacks(self, value):
#             if value <= 0:
#                 raise serializers.ValidationError("Number of sacks must be greater than 0")
#             return value
#
#         def validate_rent_per_sack(self, value):
#             if value is not None and value <= 0:
#                 raise serializers.ValidationError("Rent per sack must be greater than 0")
#             return value
#
#     # Main bulk serializer
#     details = CertificateDetailItemSerializer(many=True)
#
#     def validate_details(self, value):
#         if not value:
#             raise serializers.ValidationError("At least one detail is required")
#
#         if len(value) > 1000:  # Limit bulk size
#             raise serializers.ValidationError("Cannot create more than 1000 details at once")
#
#         # Check for duplicate composite keys in the batch
#         seen_keys = set()
#         for i, detail in enumerate(value):
#             key = (
#                 detail.get('business_id').business_id if detail.get('business_id') else None,
#                 detail.get('token_no'),
#                 detail.get('xitem'),
#                 detail.get('xunit'),
#                 detail.get('xfloor'),
#                 detail.get('xpocket')
#             )
#
#             if key in seen_keys:
#                 raise serializers.ValidationError({
#                     f'details[{i}]': f"Duplicate certificate detail found at index {i}"
#                 })
#             seen_keys.add(key)
#
#         return value
#
#     def validate(self, data):
#         """Additional validation for the entire batch"""
#         request = self.context['request']
#         user = request.user
#         token_no = self.context['token_no']
#
#         # Resolve business_id from logged-in user
#         try:
#             business_id = CompanyProfile.objects.get(pk=user.business_id).business_id
#         except CompanyProfile.DoesNotExist:
#             raise serializers.ValidationError("User business profile not found")
#
#         details = data.get('details', [])
#
#         # Check if any of these composite keys already exist in database
#         existing_keys = []
#         for i, detail in enumerate(details):
#             existing = CertificateDetails.objects.filter(
#                 business_id=business_id,
#                 token_no=token_no,
#                 xitem=detail.get('xitem'),
#                 xunit=detail.get('xunit'),
#                 xfloor=detail.get('xfloor'),
#                 xpocket=detail.get('xpocket')
#             ).exists()
#
#             if existing:
#                 existing_keys.append(i)
#
#         if existing_keys:
#             raise serializers.ValidationError({
#                 'details': f"Certificate details at indexes {existing_keys} already exist in database"
#             })
#
#         return data
#
#     def create(self, validated_data):
#         details_data = validated_data['details']
#         created_details = []
#         user = self.context['request'].user
#         token_no = self.context['token_no']
#         current_time = timezone.now()
#
#
#         with transaction.atomic():
#             for detail_data in details_data:
#                 # Auto-calculate total_rent
#                 if detail_data.get('number_of_sacks') and detail_data.get('rent_per_sack'):
#                     detail_data['total_rent'] = (
#                             detail_data['number_of_sacks'] * detail_data['rent_per_sack']
#                     )
#
#                 # Set audit fields
#                 detail_data['created_by'] = user
#                 detail_data['created_at'] = current_time
#                 detail_data['token_no'] = token_no
#
#                 detail = CertificateDetails.objects.create(**detail_data)
#                 created_details.append(detail)
#
#         return created_details


class CertificateDetailsBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating certificate details"""

    # Individual detail serializer without business_id
    class CertificateDetailItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = CertificateDetails
            fields = [
                'certificate_no',
                'xitem',
                'xunit',
                'xfloor',
                'xpocket',
                'potato_type',
                'number_of_sacks',
                'rent_per_sack'
            ]

        def validate_number_of_sacks(self, value):
            if value <= 0:
                raise serializers.ValidationError("Number of sacks must be greater than 0")
            return value

        def validate_rent_per_sack(self, value):
            if value is not None and value <= 0:
                raise serializers.ValidationError("Rent per sack must be greater than 0")
            return value

    # Main bulk serializer
    details = CertificateDetailItemSerializer(many=True)

    def validate_details(self, value):
        if not value:
            raise serializers.ValidationError("At least one detail is required")

        if len(value) > 1000:  # Limit bulk size
            raise serializers.ValidationError("Cannot create more than 1000 details at once")

        # Check for duplicate composite keys in the batch
        seen_keys = set()
        token_no = self.context['token_no']
        user = self.context['request'].user

        # Resolve business_id from user
        from masterdata.models import CompanyProfile
        try:
            business_id = CompanyProfile.objects.get(pk=user.business_id).business_id
        except CompanyProfile.DoesNotExist:
            raise serializers.ValidationError("User business profile not found")

        for i, detail in enumerate(value):
            key = (
                business_id,
                token_no,
                detail.get('xitem'),
                detail.get('xunit'),
                detail.get('xfloor'),
                detail.get('xpocket')
            )

            if key in seen_keys:
                raise serializers.ValidationError({
                    f'details[{i}]': f"Duplicate certificate detail found at index {i}"
                })
            seen_keys.add(key)

        return value

    def validate(self, data):
        """Additional validation for the entire batch"""
        request = self.context['request']
        user = request.user
        token_no = self.context['token_no']

        from masterdata.models import CompanyProfile
        try:
            business_id = CompanyProfile.objects.get(pk=user.business_id).business_id
        except CompanyProfile.DoesNotExist:
            raise serializers.ValidationError("User business profile not found")

        details = data.get('details', [])

        # Check if any composite keys already exist in DB
        existing_keys = []
        for i, detail in enumerate(details):
            existing = CertificateDetails.objects.filter(
                business_id=business_id,
                token_no=token_no,
                xitem=detail.get('xitem'),
                xunit=detail.get('xunit'),
                xfloor=detail.get('xfloor'),
                xpocket=detail.get('xpocket')
            ).exists()

            if existing:
                existing_keys.append(i)

        if existing_keys:
            raise serializers.ValidationError({
                'details': f"Certificate details at indexes {existing_keys} already exist in database"
            })

        return data

    def create(self, validated_data):
        details_data = validated_data['details']
        created_details = []
        request = self.context['request']
        user = request.user
        token_no = self.context['token_no']
        current_time = timezone.now()

        # Resolve business_id automatically
        from masterdata.models import CompanyProfile
        business = CompanyProfile.objects.get(pk=user.business_id)

        with transaction.atomic():
            for detail_data in details_data:
                # Auto-fill business_id and token_no
                detail_data['business_id'] = business
                detail_data['token_no'] = token_no

                # Auto-calculate total_rent
                if detail_data.get('number_of_sacks') and detail_data.get('rent_per_sack'):
                    detail_data['total_rent'] = (
                        detail_data['number_of_sacks'] * detail_data['rent_per_sack']
                    )

                # Audit fields
                detail_data['created_by'] = user
                detail_data['created_at'] = current_time

                detail = CertificateDetails.objects.create(**detail_data)
                created_details.append(detail)

        return created_details



class CertificateDetailsResponseSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business_id.company_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = CertificateDetails
        fields = [
            'business_id',
            'business_name',
            'token_no',
            'certificate_no',
            'xitem',
            'xunit',
            'xfloor',
            'xpocket',
            'potato_type',
            'number_of_sacks',
            'rent_per_sack',
            'total_rent',
            'created_by_name',
            'created_at'
        ]