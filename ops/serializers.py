from datetime import datetime

from django.core.validators import RegexValidator

from inventory.models import Stock, Imtrn
from masterdata.models import CustomerProfile, ItemMaster, CompanyProfile
from ops.models import TokenNumber, Booking, Certificate, CertificateDetails, Opchalland, Opchallan
from rest_framework import serializers
from django.db import models, transaction
from django.utils import timezone
from .models import CertificateDetails, Certificate
from decimal import Decimal



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


class CertificateReadyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['token_no']


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


class CertificateDetailsBulkCreateSerializer(serializers.Serializer):
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
                'number_of_sacks'
            ]

        def validate_number_of_sacks(self, value):
            if value <= 0:
                raise serializers.ValidationError("Number of sacks must be greater than 0")
            return value

        # def validate_rent_per_sack(self, value):
        #     if value is not None and value <= 0:
        #         raise serializers.ValidationError("Rent per sack must be greater than 0")
        #     return value

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
            business_profile = CompanyProfile.objects.get(pk=user.business_id)
            business_id = business_profile.business_id
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

        # Import here to avoid circular imports
        from masterdata.models import CompanyProfile

        try:
            business_profile = CompanyProfile.objects.get(pk=user.business_id)
            business_id = business_profile.business_id
        except CompanyProfile.DoesNotExist:
            raise serializers.ValidationError("User business profile not found")

        details = data.get('details', [])

        # Check if any composite keys already exist in DB
        existing_keys = []
        for i, detail in enumerate(details):
            existing = CertificateDetails.objects.filter(
                business_id=business_id,  # Use business_id string/integer
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

        # ===== QUANTITY VALIDATION AGAINST CERTIFICATE =====
        # Get the certificate to validate against (Alternative approach)
        try:
            certificate = Certificate.objects.get(
                token_no=token_no,
                business_id=business_id  # Use business_id string/integer
            )
        except Certificate.DoesNotExist:
            raise serializers.ValidationError(f"Certificate {token_no} not found for your business")

        # Debug: Print certificate details (remove in production)
        print(
            f"DEBUG: Certificate {token_no} found, no_of_sack: {getattr(certificate, 'no_of_sack', 'FIELD_NOT_FOUND')}")

        # Get existing details quantity for this certificate (Alternative approach)
        existing_details_qty = CertificateDetails.objects.filter(
            business_id=business_id,  # Use business_id string/integer
            token_no=token_no
        ).aggregate(
            total_existing=models.Sum('number_of_sacks')
        )['total_existing'] or 0

        # Calculate new details quantity
        new_details_qty = sum(detail.get('number_of_sacks', 0) for detail in details)

        # Total quantity after adding new details
        total_details_qty = existing_details_qty + new_details_qty

        # Get certificate total quantity - handle different possible field names
        certificate_total_qty = getattr(certificate, 'number_of_sacks', None) or getattr(certificate, 'number_of_sacks',
                                                                                    None) or 0

        # Debug prints (remove in production)
        print(f"DEBUG: Business ID: {business_id}")
        print(f"DEBUG: Token No: {token_no}")
        print(f"DEBUG: Existing details qty: {existing_details_qty}")
        print(f"DEBUG: New details qty: {new_details_qty}")
        print(f"DEBUG: Total details qty: {total_details_qty}")
        print(f"DEBUG: Certificate total qty: {certificate_total_qty}")

        # Validate quantity constraint
        if certificate_total_qty <= 0:
            raise serializers.ValidationError({
                'details': f"Certificate {token_no} has no valid quantity set (no_of_sack: {certificate_total_qty})"
            })

        if total_details_qty > certificate_total_qty:
            raise serializers.ValidationError({
                'details': f"Total quantity in certificate details ({total_details_qty}) cannot exceed "
                           f"certificate total quantity ({certificate_total_qty}). "
                           f"Existing details quantity: {existing_details_qty}, "
                           f"New details quantity: {new_details_qty}"
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
            'business_id_id',
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


class OpchallandSerializer(serializers.ModelSerializer):
    """Serializer for Opchalland (child) model"""
    quantity = serializers.DecimalField(max_digits=20, decimal_places=6, source='xqtychl')

    class Meta:
        model = Opchalland
        fields = [
            'quantity','xunit', 'xfloor', 'xpocket', 'xqtychl'
        ]
        extra_kwargs = {'xqtychl': {'read_only': True}}


# class OpchallanSerializer(serializers.ModelSerializer):
#     # Nested serializer for child records
#     delivery_items = OpchallandSerializer(many=True, write_only=True)
#
#     class Meta:
#         model = Opchallan
#         fields = [
#             'token_no', 'xchgtot', 'xpayloan','xemptysack', 'xemptysackchgtot',
#             'xinterestamt','xfanchgtot', 'delivery_items'
#         ]
#         read_only_fields = ['xchlnum']  # Auto-generated
#
#
#     def validate(self, data):
#         """Validate that certificate exists"""
#         business_id = data.get('business_id')
#         token_no = data.get('token_no')
#         if business_id and token_no:
#             # Check if certificate exists
#             certificate_exists = Certificate.objects.filter(
#                 business_id=business_id,
#                 token_no=token_no
#             ).exists()
#
#             if not certificate_exists:
#                 raise serializers.ValidationError({
#                     'token_no': f'Certificate with business_id={business_id.id if hasattr(business_id, "id") else business_id} and token_no={token_no} does not exist'
#                 })
#
#         return data
#
#     def create(self, validated_data):
#         """Create Opchallan with related Opchalland records"""
#         delivery_items_data = validated_data.pop('delivery_items', [])
#         with transaction.atomic():
#             # Create parent Opchallan record
#             opchallan = Opchallan.objects.create(**validated_data)
#
#
#             # Create child Opchalland records
#             for index, item_data in enumerate(delivery_items_data, start=1):
#                 xqtychl = Decimal(str(item_data.get('xqtychl', 0.0)))
#                 xrate = Decimal(str(item_data.get('xrate', 0.0)))
#
#                 xdtwotax = xqtychl*xrate
#
#                 Opchalland.objects.create(
#                     xrow=index,  # auto-assign 1, 2, 3, ...
#                     business_id=validated_data['business_id'],
#                     xchlnum=opchallan.xchlnum,
#                     token_no=opchallan.token_no,
#                     xdtwotax=xdtwotax,
#                     created_by=opchallan.created_by,
#                     xitem="01-01-001-0001",
#                     **item_data
#                 )
#
#             return opchallan
#
#
#     def to_representation(self, instance):
#         """Include delivery items in response"""
#         data = super().to_representation(instance)
#
#         # Add delivery items to response
#         delivery_items = Opchalland.objects.filter(
#             business_id=instance.business_id,
#             xchlnum=instance.xchlnum,
#             token_no=instance.token_no
#         )
#         data['delivery_items'] = OpchallandSerializer(delivery_items, many=True).data
#         data['xchlnum'] = instance.xchlnum  # Include auto-generated number
#
#         return data


class OpchallanSerializer(serializers.ModelSerializer):
    delivery_items = OpchallandSerializer(many=True, write_only=True)

    class Meta:
        model = Opchallan
        fields = [
            'token_no', 'xchgtot', 'xpayloan', 'xemptysack', 'xemptysackchgtot',
            'xinterestamt', 'xfanchgtot', 'delivery_items',
            'business_id', 'created_by'  # Explicitly include these fields
        ]
        read_only_fields = ['xchlnum', 'created_by', 'business_id']

    def _create_stock_out_entries(self, delivery_item, challan, business, user):
        """Create stock transaction entries for delivery"""
        current_datetime = datetime.now()

        # Stock OUT entry (from source location) - Negative quantity
        out_entry = Imtrn(
            business_id=business,
            xunit=delivery_item.xunit,
            xfloor=delivery_item.xfloor,
            xpocket=delivery_item.xpocket,
            xitem="01-01-001-0001",  # Using the default item code from your challan
            xdate=current_datetime.date(),
            xyear=current_datetime.year,
            xper=self._calculate_period(current_datetime),
            xqty=delivery_item.xqtychl,  # Negative for outgoing
            xval=0,  # You might want to calculate value based on rate
            xdocnum=challan.xchlnum,
            token_no=challan.token_no,
            xdoctype="CHL",  # Challan
            xaction="Delivery Out",
            xsign=-1,  # Negative sign for outgoing
            xdocrow=delivery_item.xrow,
            xtime=current_datetime,
            created_by=user,
            created_at=current_datetime,
            updated_at=current_datetime,
        )
        out_entry.save()

    def _calculate_period(self, date):
        """Calculate period based on your business logic"""
        return (date.month + 6) % 12 or 12

    def validate(self, data):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Request context with user is required")

        # Get business profile
        try:
            business = CompanyProfile.objects.get(pk=request.user.business_id)
            self.context['business'] = business
        except CompanyProfile.DoesNotExist:
            raise serializers.ValidationError("Business profile not found")

        # Get certificate and rate
        token_no = data.get('token_no')
        if not token_no:
            raise serializers.ValidationError("Token number is required")

        try:
            certificate = Certificate.objects.get(
                token_no=token_no,
                business_id=business
            )
            self.context['certificate'] = certificate
        except Certificate.DoesNotExist:
            raise serializers.ValidationError({
                'token_no': 'Certificate not found for the given token number'
            })

        # Validate stock for each delivery item
        delivery_items_data = data.get('delivery_items', [])
        for item_data in delivery_items_data:
            xunit = item_data.get('xunit')
            xfloor = item_data.get('xfloor')
            xpocket = item_data.get('xpocket')
            xqtychl = Decimal(str(item_data.get('xqtychl', '0.0')))

            if xunit and xfloor and xpocket:
                stock_obj = Stock.objects.filter(
                    token_no=token_no,
                    xunit=xunit,
                    xfloor=xfloor,
                    xpocket=xpocket
                ).first()

                current_stock = stock_obj.number_of_sacks if stock_obj and stock_obj.number_of_sacks is not None else 0

                if current_stock < xqtychl:
                    raise serializers.ValidationError({
                        'delivery_items': f'Insufficient stock for unit {xunit}, floor {xfloor}, pocket {xpocket}. '
                                          f'Available: {current_stock}, Requested: {xqtychl}'
                    })

        return data

    def create(self, validated_data):
        delivery_items_data = validated_data.pop('delivery_items', [])
        request = self.context.get('request')
        business = self.context.get('business')
        certificate = self.context.get('certificate')
        xrate = certificate.rent_per_sack

        with transaction.atomic():
            # Create parent record with all required fields
            opchallan = Opchallan.objects.create(
                **validated_data,
                created_by=request.user if request else None,
                business_id=business,
                xcus=certificate.customer_code,
                xmobile=certificate.xmobile,
                xcur='BDT'
            )

            # Calculate item amounts and total
            item_total_amount = Decimal('0.0')
            for index, item_data in enumerate(delivery_items_data, start=1):
                xqtychl = Decimal(str(item_data.get('xqtychl', '0.0')))
                item_amount = xqtychl * xrate
                item_total_amount += item_amount

                delivery_item = Opchalland.objects.create(
                    xrow=index,
                    business_id=business,
                    xchlnum=opchallan.xchlnum,
                    token_no=opchallan.token_no,
                    xdtwotax=item_amount,
                    xlineamt=item_amount,
                    xrate=xrate,
                    created_by=opchallan.created_by,
                    xitem="01-01-001-0001",
                    **item_data
                )

                # Create stock out entry
                self._create_stock_out_entries(delivery_item, opchallan, business, request.user)

            # Get all additional amounts
            xchgtot = Decimal(str(request.data.get('xchgtot', '0.0')))
            xemptysackchgtot = Decimal(str(request.data.get('xemptysackchgtot', '0.0')))
            xfanchgtot = Decimal(str(request.data.get('xfanchgtot', '0.0')))
            xinterestamt = Decimal(str(request.data.get('xinterestamt', '0.0')))
            xpayloan = Decimal(str(request.data.get('xpayloan', '0.0')))

            # Calculate final total (items + charges + interest) - payment
            total_amount = (item_total_amount + xchgtot + xemptysackchgtot + xfanchgtot + xinterestamt) - xpayloan

            # Update amounts in the challan
            opchallan.xtotamt = total_amount
            opchallan.xstatus = "Issued"
            opchallan.save()

            return opchallan

    def to_representation(self, instance):
        """Include delivery items in response"""
        data = super().to_representation(instance)

        # Add delivery items to response
        delivery_items = Opchalland.objects.filter(
            business_id=instance.business_id,
            xchlnum=instance.xchlnum,
            token_no=instance.token_no
        )
        data['delivery_items'] = OpchallandSerializer(delivery_items, many=True).data
        data['xchlnum'] = instance.xchlnum  # Include auto-generated number

        return data
