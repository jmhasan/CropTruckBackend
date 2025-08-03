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
                xstatus='Counted'
            )
            return token
        except TokenNumber.DoesNotExist:
            raise ValidationError(f"Token {token_no} is not Counted or already used for this business.")

    @staticmethod
    def get_or_create_customer(xmobile, customer_data):
        """Get existing customer by xmobile or create new one"""
        try:
            # Try to get existing customer
            customer = CustomerProfile.objects.get(xmobile=xmobile)
            # Update customer data if provided
            print(customer)
            if customer_data:
                for key, value in customer_data.items():
                    if value and hasattr(customer, key):
                        setattr(customer, key, value)
                customer.save()
            return customer, False  # False means not created
        except CustomerProfile.DoesNotExist:
            # Create new customer
            print("create customer called")
            customer = CustomerProfile.objects.create(
                xmobile=xmobile,
                **customer_data
            )
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
            'customer_code': validated_data.get('customer_code', ''),
            'father_name': validated_data.get('father_name', ''),
            'division_name': validated_data.get('division_name', ''),
            'district_name': validated_data.get('district_name', ''),
            'upazila_name': validated_data.get('upazila_name', ''),
            'union_name': validated_data.get('union_name', ''),
            'village': validated_data.get('village', ''),
            'post_office': validated_data.get('post_office', '')
        }

        # Remove empty values
        customer_data = {k: v for k, v in customer_data.items() if v}

        # Step 3: Get or create customer profile
        customer, is_new_customer = CertificateService.get_or_create_customer(xmobile, customer_data)

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
            'created_at': timezone.now(),
            'updated_at': timezone.now()
        }

        certificate = Certificate.objects.create(**certificate_data)

        # Step 5: Mark token as used
        xstatus='Completed'
        token.save()

        return {
            'certificate': certificate,
            'customer': customer,
            'is_new_customer': is_new_customer,
            'business': business
        }