from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from masterdata.models import CustomerProfile
from ops.models import TokenNumber, Certificate


class CertificateService:

    @staticmethod
    def validate_token(business_id, token_no):
        """Validate if token exists and is available for use"""
        try:
            token = TokenNumber.objects.get(
                business_id_id=business_id,
                token_no=token_no,
                xstatus='Counted'  # Check if status is available
            )
            return token
        except TokenNumber.DoesNotExist:
            raise ValidationError(f"Token {token_no} is not available or already used for this business.")

    @staticmethod
    def generate_customer_code(business_id):
        """Generate next customer code for business"""
        # Get the last customer code for this business
        last_customer = CustomerProfile.objects.filter(
            business_id=business_id
        ).order_by('-customer_code').first()

        if last_customer and last_customer.customer_code:
            # Extract number from last code (assuming format like CUS-000001)
            try:
                last_number = int(last_customer.customer_code.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        # Format as CUS-000001
        return f"CUS-{next_number:06d}"

    @staticmethod
    def get_or_create_customer(business, xmobile, customer_data):
        """Get existing customer by xmobile and business or create new one"""
        if not xmobile:
            raise ValidationError("Mobile number (xmobile) is required.")

        try:
            # Try to get existing customer for this business and mobile
            customer = CustomerProfile.objects.get(
                business_id=business,
                xmobile=xmobile
            )
            # Update customer data if provided and customer is active
            if customer_data and customer.is_active:
                for key, value in customer_data.items():
                    if value and hasattr(customer, key):
                        setattr(customer, key, value)
                customer.save()
            return customer, False  # False means not created
        except CustomerProfile.DoesNotExist:
            # Generate customer code
            customer_code = CertificateService.generate_customer_code(business.pk)

            # Create new customer with business_id and generated customer_code
            customer_data_with_code = {
                'business_id': business,
                'customer_code': customer_code,
                'xmobile': xmobile,
                **customer_data
            }

            customer = CustomerProfile.objects.create(**customer_data_with_code)
            return customer, True  # True means created

    @staticmethod
    @transaction.atomic
    def create_certificate(validated_data, user):
        """Create certificate with token validation and customer management"""

        # Get business from user profile
        from masterdata.models import CompanyProfile
        try:
            business = CompanyProfile.objects.get(pk=user.business_id)
        except CompanyProfile.DoesNotExist:
            raise ValidationError("User business profile not found.")

        # Extract required fields
        business_id = business.pk
        token_no = validated_data.get('token_no')
        xmobile = validated_data.get('xmobile')

        # Step 1: Validate token availability
        token = CertificateService.validate_token(business_id, token_no)

        # Step 2: Prepare customer data
        customer_data = {
            'customer_name': validated_data.get('customer_name', ''),
            'contact_person': validated_data.get('contact_person', ''),
            'xphone': validated_data.get('xphone', ''),
            'xemail': validated_data.get('xemail', ''),
            'father_name': validated_data.get('father_name', ''),
            'division_name': validated_data.get('division_name', ''),
            'district_name': validated_data.get('district_name', ''),
            'upazila_name': validated_data.get('upazila_name', ''),
            'union_name': validated_data.get('union_name', ''),
            'village': validated_data.get('village', ''),
            'post_office': validated_data.get('post_office', ''),
            'postal_code': validated_data.get('postal_code', ''),
            'xaddress': validated_data.get('xaddress', ''),
            'customer_type': validated_data.get('customer_type', 'Farmer'),
            'trade_license_number': validated_data.get('trade_license_number', ''),
            'bin_number': validated_data.get('bin_number', ''),
            'tin_number': validated_data.get('tin_number', ''),
            'credit_limit': validated_data.get('credit_limit'),
            'credit_terms_days': validated_data.get('credit_terms_days'),
            'default_discount': validated_data.get('default_discount'),
            'group_name': validated_data.get('group_name', ''),
            'remarks': validated_data.get('remarks', ''),
            'created_by': user,
            'created_at': timezone.now()
        }

        # Remove empty values
        customer_data = {k: v for k, v in customer_data.items() if v}

        # Step 3: Get or create customer profile
        customer, is_new_customer = CertificateService.get_or_create_customer(business, xmobile, customer_data)

        # Step 4: Create certificate with customer information
        certificate_data = {
            'business_id': business,  # Use the business object
            'token_no': token_no,
            'certificate_no': validated_data.get('certificate_no'),
            'booking_no': validated_data.get('booking_no'),
            'customer_code': customer.customer_code,
            'customer_name': customer.customer_name,
            'xmobile': customer.xmobile,
            'father_name': customer.father_name,
            'division_name': customer.division_name,
            'district_name': customer.district_name,
            'upazila_name': customer.upazila_name,
            'union_name': customer.union_name,
            'village': customer.village,
            'post_office': customer.post_office,
            'number_of_sacks': validated_data.get('number_of_sacks'),
            'potato_type': validated_data.get('potato_type'),
            'rent_per_sack': validated_data.get('rent_per_sack'),
            'total_rent': validated_data.get('total_rent'),
            'advance_rent': validated_data.get('advance_rent'),
            'remaining_rent': validated_data.get('remaining_rent'),
            'number_of_empty_sacks': validated_data.get('number_of_empty_sacks'),
            'price_of_empty_sacks': validated_data.get('price_of_empty_sacks'),
            'transportation': validated_data.get('transportation'),
            'given_loan': validated_data.get('given_loan'),
            'total_amount_taka': validated_data.get('total_amount_taka'),
            'created_by': user,
            'created_at': timezone.now()
        }

        certificate = Certificate.objects.create(**certificate_data)

        # Step 5: Mark token as used
        token.xstatus = 'Completed'
        token.updated_by = user
        token.updated_at = timezone.now()
        token.save()

        return {
            'certificate': certificate,
            'customer': customer,
            'is_new_customer': is_new_customer,
            'business': business
        }