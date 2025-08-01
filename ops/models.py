import datetime
from math import trunc

from django.core.validators import RegexValidator
from django.db import models

from masterdata.models import AuditModel, CompanyProfile, CustomerProfile

import datetime

def booking_no():
    # Get current year and extract the last two digits (e.g., 2025 → "25")
    year_suffix = datetime.date.today().strftime('%y')
    prefix = f'B{year_suffix}-'

    # Get last booking_no with that prefix
    last_booking = Booking.objects.filter(booking_no__startswith=prefix).order_by('booking_no').last()

    # Default serial number
    next_serial = 1

    if last_booking:
        # Extract last 5-digit serial part and increment
        try:
            last_serial = int(last_booking.booking_no.split('-')[1])
            next_serial = last_serial + 1
        except (IndexError, ValueError):
            pass  # Just fall back to default if something goes wrong

    booking_number = f"{prefix}{next_serial:05d}"
    return booking_number


def token_no():
    # GET Current Date
    today = datetime.date.today()
    # Format the date like (20-11 YY-MM)
    today_string = today.strftime('%y%m')
    # For the very first time invoice_number is YY-MM-DD-001
    next_invoice_number = '000001'
    # Get Last Invoice Number of Current Year, Month and Day (20-11-28 YY-MM-DD)
    last_invoice = Booking.objects.filter(booking_no__startswith=today_string).order_by('booking_no').last()

    if last_invoice:
        # Cut 4 digit from the left and converted to int (2011:xxx)
        last_invoice_number = int(last_invoice.booking_no[4:])
        # Increment one with last six digit
        next_invoice_number = '{0:06d}'.format(last_invoice_number + 1)
    # Return custom invoice number
    return today_string + next_invoice_number

class Booking(AuditModel):
    pk = models.CompositePrimaryKey('business_id', 'booking_no')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    booking_no = models.CharField(max_length=50, default=booking_no)
    customer_code = models.CharField(max_length=50,blank=True, null=True)
    xmobile = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^01[3-9]\d{8}$',
                message='Enter a valid Bangladeshi mobile number (e.g. 017XXXXXXXX).'
            )
        ]
    )
    xname = models.TextField(max_length=150)
    father_name = models.TextField(max_length=100, blank=True, null=True)
    district_name = models.TextField(max_length=100, blank=True, null=True)
    division_name = models.TextField(max_length=100, blank=True, null=True)
    upazila_name = models.TextField(max_length=100, blank=True, null=True)
    union_name = models.TextField(max_length=100, blank=True, null=True)
    village = models.TextField(max_length=100, blank=True, null=True)
    post_office = models.TextField(max_length=100, blank=True, null=True)
    xadvance = models.DecimalField(max_digits=20, decimal_places=4, default=0.00)
    xsack = models.IntegerField(default=0.00)


    class Meta:
        db_table = 'booking'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        return f"{self.booking_no}"

class TokenNumber(AuditModel):
    pk = models.CompositePrimaryKey('business_id', 'token_no')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    token_no = models.CharField(max_length=10)
    xsack = models.IntegerField(default=0.00)
    xstatus = models.CharField(max_length=50,default='Pending')

    class Meta:
        db_table = 'token_number'
        verbose_name = 'Token Number'
        verbose_name_plural = 'Token Numbers'



class Certificate(AuditModel):
    pk = models.CompositePrimaryKey('business_id', 'certificate_no', 'customer_code', 'token_no')

    customer = models.ForeignObject(
        CustomerProfile,
        on_delete=models.CASCADE,
        from_fields=("business_id", "customer_code"),
        to_fields=("business_id", "customer_code"),
    )

    customer = models.ForeignObject(
        CustomerProfile,
        on_delete=models.CASCADE,
        from_fields=("business_id", "customer_code"),
        to_fields=("business_id", "customer_code"),
    )

    business_id = models.ForeignKey(CompanyProfile, on_delete=models.SET_NULL, blank=True, null=True)
    certificate_no = models.ForeignKey(TokenNumber, on_delete=models.DO_NOTHING)   # e.g., C2507-10254
    customer_code = models.ForeignKey(CustomerProfile, on_delete=models.DO_NOTHING )
    token_no = models.ForeignKey(max_length=10, on_delete=models.DO_NOTHING, blank=True, null=True)
    booking_no = models.ForeignKey(max_length=50,on_delete=models.DO_NOTHING, blank=True, null=True)
    xmobile = models.CharField(max_length=20, blank=True, null=True)



    father_name = models.CharField(max_length=150, blank=True, null=True)
    division_name = models.CharField(max_length=100, blank=True, null=True)
    district_name = models.CharField(max_length=100, blank=True, null=True)
    upazila_name = models.CharField(max_length=100, blank=True, null=True)
    union_name = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=150, blank=True, null=True)
    post_office = models.CharField(max_length=100, blank=True, null=True)


    number_of_sacks = models.PositiveIntegerField(default=0)
    potato_type = models.CharField(max_length=100, blank=True, null=True)  # Could be FK if you have a PotatoType table
    rent_per_sack = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_rent = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    advance_rent = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    remaining_rent = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    number_of_empty_sacks = models.PositiveIntegerField(default=0)
    price_of_empty_sacks = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    transportation = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    given_loan = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_amount_taka = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)


    class Meta:
        db_table = 'certificate'
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'

    def __str__(self):
        return self.certificate_no



