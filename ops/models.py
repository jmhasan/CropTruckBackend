import datetime
from math import trunc

from django.core.validators import RegexValidator
from django.db import models, transaction

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
    xstatus = models.CharField(max_length=50, default='Pending')


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


class Certificate(models.Model):
    pk = models.CompositePrimaryKey('business_id', 'token_no')

    # Use correct app_label.ModelName
    business_id = models.ForeignKey('masterdata.CompanyProfile', on_delete=models.DO_NOTHING)
    token_no = models.CharField(max_length=10)

    certificate_no = models.CharField(max_length=20, blank=True, null=True)
    booking_no = models.CharField(max_length=50, blank=True, null=True)
    customer_code = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=255)
    xmobile = models.CharField(max_length=20, blank=True, null=True)
    father_name = models.CharField(max_length=150, blank=True, null=True)
    division_name = models.CharField(max_length=100, blank=True, null=True)
    district_name = models.CharField(max_length=100, blank=True, null=True)
    upazila_name = models.CharField(max_length=100, blank=True, null=True)
    union_name = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=150, blank=True, null=True)
    post_office = models.CharField(max_length=100, blank=True, null=True)

    number_of_sacks = models.IntegerField()
    potato_type = models.CharField(max_length=100, blank=True, null=True)
    rent_per_sack = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_rent = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    advance_rent = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    remaining_rent = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    number_of_empty_sacks = models.IntegerField()
    price_of_empty_sacks = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    transportation = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    given_loan = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_amount_taka = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    # Correct references to the user model
    created_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING, related_name='certificate_updated_by_set', blank=True, null=True)

    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    xstatus = models.CharField(max_length=50,default='Open')

    posted_by = models.IntegerField()
    posted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'certificate'

    def __str__(self):
        return str(self.token_no)


class CertificateDetails(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'token_no', 'xitem', 'xunit', 'xfloor', 'xpocket')
    business_id = models.ForeignKey('masterdata.CompanyProfile', on_delete=models.DO_NOTHING)
    token_no = models.CharField(max_length=10)
    certificate_no = models.CharField(max_length=20, blank=True, null=True)
    xitem = models.CharField(max_length=50, default='01-01-001-0001')
    xunit = models.CharField(max_length=100)
    xfloor = models.CharField(max_length=100)
    xpocket = models.CharField(max_length=100)
    potato_type = models.CharField(max_length=100, blank=True, null=True)
    number_of_sacks = models.IntegerField()
    rent_per_sack = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_rent = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    created_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING,
                                   related_name='certificate_details_updated_by_set', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'certificate_details'


class Opchallan(models.Model):
    @staticmethod
    def generate_delivery_number():
        """Generate unique transfer order number with format TO-YY-XXXXXX"""
        with transaction.atomic():
            year_str = datetime.date.today().strftime('%y')
            prefix = f"CL-{year_str}-"

            # Use select_for_update to prevent race conditions
            last_entry = (Opchallan.objects
                          .filter(xchlnum__startswith=prefix)
                          .select_for_update()
                          .order_by('-xchlnum')
                          .first())

            if last_entry:
                try:
                    last_code = int(last_entry.ximtor.split('-')[-1])
                    next_number = f"{last_code + 1:06d}"
                except (ValueError, IndexError):
                    # Fallback if parsing fails
                    next_number = "000001"
            else:
                next_number = "000001"

            return prefix + next_number
    pk = models.CompositePrimaryKey('business_id_id', 'xchlnum', 'token_no')
    business_id = models.ForeignKey('masterdata.CompanyProfile', models.DO_NOTHING)
    xchlnum = models.CharField(max_length=100, default=generate_delivery_number)
    token_no = models.CharField(max_length=100)
    xmobile = models.CharField(max_length=20, blank=True, null=True)
    certificate_no = models.CharField(max_length=20, blank=True, null=True)
    xcus = models.CharField(max_length=100, blank=True, null=True)
    xwh = models.CharField(max_length=100, blank=True, null=True)
    xcur = models.CharField(max_length=100, blank=True, null=True)
    xdelsite = models.CharField(max_length=250, blank=True, null=True)
    xvehicle = models.CharField(max_length=100, blank=True, null=True)
    xdriver = models.CharField(max_length=150, blank=True, null=True)
    xdriver_mobile = models.CharField(max_length=150, blank=True, null=True)
    xdtwotax = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xadvance = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xempttot = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xchgtot = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xdestin = models.CharField(max_length=100, blank=True, null=True)
    xtotamt = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xstatus = models.CharField(default='Open',max_length=100, blank=True, null=True)
    confirm_by = models.ForeignKey('user.CustomUser', models.DO_NOTHING, db_column='confirm_by', blank=True, null=True)
    confirm_at = models.DateTimeField(blank=True, null=True)
    invoice_by = models.ForeignKey('user.CustomUser', models.DO_NOTHING, db_column='invoice_by', related_name='opchallan_invoice_by_set', blank=True, null=True)
    invoice_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey('user.CustomUser', models.DO_NOTHING, related_name='opchallan_created_by_set', blank=True, null=True)
    updated_by = models.ForeignKey('user.CustomUser', models.DO_NOTHING, related_name='opchallan_updated_by_set', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'opchallan'

    def __str__(self):
        return str(self.xchlnum)


class Opchalland(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xchlnum', 'token_no', 'xrow')
    business_id = models.ForeignKey('masterdata.CompanyProfile', models.DO_NOTHING)
    xchlnum = models.CharField(max_length=100)
    token_no = models.CharField(max_length=100)
    xrow = models.IntegerField()
    xitem = models.CharField(max_length=100)
    xunit = models.CharField(max_length=50, blank=True, null=True)
    xfloor = models.CharField(max_length=50, blank=True, null=True)
    xpocket = models.CharField(max_length=50, blank=True, null=True)
    xqtychl = models.DecimalField(max_digits=20, decimal_places=3, blank=True, null=True)
    xrate = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    xemptysack = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xemptsrate = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xadvance = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xchgdel = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xchgtot = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xinterest = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xinterestamt = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xdtwotax = models.DecimalField(max_digits=30, decimal_places=6, blank=True, null=True)
    xwh = models.CharField(max_length=100, blank=True, null=True)
    xunitsel = models.CharField(max_length=100, blank=True, null=True)
    xcfsel = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    xcur = models.CharField(max_length=100, blank=True, null=True)
    xdisc = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    xlineamt = models.DecimalField(max_digits=30, decimal_places=6, blank=True, null=True)
    created_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, related_name='opchalland_updated_by_set', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'opchalland'
