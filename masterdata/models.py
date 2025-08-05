import datetime
from django.db import models
from user.models import CustomUser
# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

class CompanyProfile(models.Model):
    business_id = models.AutoField(primary_key=True)
    business_name = models.CharField(max_length=255)  # Full legal name
    short_name = models.CharField(max_length=100, blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    # Contact Info
    address = models.TextField()
    xphone = models.CharField(max_length=20, blank=True)
    xemail = models.EmailField(blank=True)
    xwebsite = models.URLField(blank=True, null=True)

    # Legal/Financial Info
    registration_no = models.CharField(max_length=100, blank=True, null=True)
    bin_number = models.CharField(max_length=100, blank=True, null=True)
    tin_number = models.CharField(max_length=100, blank=True, null=True)
    trade_license_no = models.CharField(max_length=100, blank=True, null=True)

    # Metadata
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser,related_name='company_created_profiles',on_delete=models.SET_NULL,
                                   null=True, blank=True)
    updated_by = models.ForeignKey(CustomUser, related_name='company_updated_profiles', on_delete=models.SET_NULL,
                                   null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "company_profile"
        verbose_name = 'Company Profile'
        verbose_name_plural = 'Company Profiles'


    def __str__(self):
        return f"{self.business_id} - {self.business_name}"

User = get_user_model()

class AuditModel(models.Model):
    create_date = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        related_name="%(class)s_created_by",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        User,
        related_name="%(class)s_updated_by",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# core/models.py or common/models.py
class CommonCodes(AuditModel):
    pk = models.CompositePrimaryKey('business_id', 'xtype','xcode')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    xtype = models.CharField(max_length=100)  # e.g., 'BANK', 'ZONE', 'DEPARTMENT'
    xcode = models.TextField(max_length=200)
    xdesc = models.TextField(max_length=250, blank=True, null=True)
    xremark = models.TextField(max_length=100, blank=True, null=True)
    zactive = models.BooleanField(default=True)

    class Meta:
        db_table = 'commoncodes'
        verbose_name = 'Common Code'
        verbose_name_plural = 'Common Codes'

    def __str__(self):
        return f"{self.xtype} - {self.xdesc}"

def cus_code():
    cusprifix = "CRT-"
    # For the very first time invoice_number is YY-MM-DD-001
    next_cus_code = '000001'
    # Get Last Invoice Number of Current Year, Month and Day (20-11-28 YY-MM-DD)
    last_customer = CustomerProfile.objects.filter(customer_code__startswith=cusprifix).order_by('customer_code').last()
    if last_customer:
        # Cut 4 digit from the left and converted to int (2011:xxx)
        last_cus_code = int(last_customer.customer_code[4:])
        # Increment one with last six digit
        next_cus_code = '{0:06d}'.format(last_cus_code + 1)
    # Return custom invoice number
    return cusprifix + next_cus_code


class CustomerProfile(AuditModel):
    # Identification
    pk = models.CompositePrimaryKey('business_id', 'customer_code')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    customer_code = models.CharField(max_length=50, default=cus_code)
    customer_name = models.CharField(max_length=255)  # Business/Customer Name
    contact_person = models.CharField(max_length=100, blank=True, null=True)

    # Contact Information
    xphone = models.CharField(max_length=20, blank=True, null=True)
    xmobile = models.CharField(max_length=20, blank=True, null=True)
    xemail = models.EmailField(blank=True, null=True)
    xwebsite = models.URLField(blank=True, null=True)

    # Personal Details
    father_name = models.TextField(max_length=100, blank=True, null=True)
    division_name = models.TextField(max_length=100, blank=True, null=True)
    district_name = models.TextField(max_length=100, blank=True, null=True)
    upazila_name = models.TextField(max_length=100, blank=True, null=True)
    union_name = models.TextField(max_length=100, blank=True, null=True)
    village = models.TextField(max_length=100, blank=True, null=True)
    post_office = models.TextField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True)
    # Address
    xaddress = models.CharField(max_length=255, blank=True, null=True)

    # Business/Legal Details
    trade_license_number = models.CharField(max_length=100, blank=True, null=True)
    bin_number = models.CharField(max_length=100, blank=True, null=True)
    tin_number = models.CharField(max_length=100, blank=True, null=True)

    # Financial Details
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    credit_terms_days = models.PositiveIntegerField(blank=True, null=True)
    default_discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    # Classification
    customer_type = models.CharField(max_length=50, choices=[
        ('Farmer', 'Farmer'),
        ('Retailer', 'Retailer'),
        ('Dealer', 'Dealer'),
        ('Corporate', 'Corporate'),
        ('Trader', 'Trader'),
        ('Agent', 'Agent'),
    ], default='Farmer')

    group_name = models.CharField(max_length=100, blank=True, null=True)

    # System Fields
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'customer_profile'
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'
        ordering = ['customer_code']

        unique_together = (('business_id', 'customer_code', 'xmobile'),)
        indexes = [
            models.Index(fields=['business_id', 'customer_code', 'xmobile']),
        ]

    def __str__(self):
        return f"{self.customer_code} - {self.customer_name}"


class GeoLocation(models.Model):
    pk = models.CompositePrimaryKey('business_id', 'division_name', 'district_name','upazila_name','union_name')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    division_name = models.CharField(max_length=100)
    division_bn = models.TextField(max_length=100)
    district_name = models.CharField(max_length=100)
    district_bn = models.TextField(max_length=100)
    upazila_name = models.CharField(max_length=100)
    upazila_bn = models.TextField(max_length=100)
    union_name = models.CharField(max_length=100)
    union_bn = models.TextField(max_length=100)

    class Meta:
        db_table = 'geo_locations'
        verbose_name = 'Geo Location'
        verbose_name_plural = 'Geo Locations'

    def __str__(self):
        return f"{self.union_name}, {self.upazila_name}"


class ItemMaster(AuditModel):
    pk = models.CompositePrimaryKey('business_id', 'xitem')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    xitem = models.CharField(max_length=50, verbose_name="Item Code")
    xname = models.CharField(max_length=200, verbose_name="Item Name")
    xdesc = models.TextField(blank=True, null=True, verbose_name="Description")
    xstype = models.TextField(default='Stock', verbose_name="Stock Type")
    xhscode = models.TextField(blank=True, null=True,  verbose_name="H.S. Code")
    xsku = models.CharField(max_length=100, blank=True, null=True,  verbose_name="SKU")
    xbarcode = models.CharField(max_length=100, blank=True,  null=True, verbose_name="Barcode")
    xgroup = models.CharField(max_length=50, default='FG', verbose_name="Item Group")
    xclass = models.CharField(max_length=50,  default='FG', verbose_name="Item Class")
    xcategory = models.CharField(max_length=50, default='FG', verbose_name="Item Category")
    xtype = models.CharField(max_length=50,  default='FG', verbose_name="Item Type",blank=True, null=True)
    xbrand = models.CharField(max_length=100, default='FG', verbose_name="Brand", blank=True, null=True)
    # Unit
    xunitpur = models.CharField(max_length=50, default='KG', verbose_name="Purchase Unit",blank=True, null=True)
    xunitstk = models.CharField(max_length=50, default='KG', verbose_name="Stock Unit", blank=True, null=True)
    xunitsel = models.CharField(max_length=50, default='KG', verbose_name="Selling Unit", blank=True, null=True)
    xunitpck = models.CharField(max_length=50, default='KG', verbose_name="Packaging Unit", blank=True, null=True)
    xunitiss = models.CharField(max_length=50, default='KG', verbose_name="Issue Unit",blank=True, null=True)
    # Conversion factor
    xcfpur = models.DecimalField(max_digits=20, decimal_places=4, default=0.00,
                                 verbose_name="Conversion factor Purchase",blank=True, null=True)
    xcfsta = models.DecimalField(max_digits=20, decimal_places=4, default=0.00, verbose_name="Conversion factor Stock",blank=True, null=True)
    xcfsel = models.DecimalField(max_digits=20, decimal_places=4, default=0.00, verbose_name="Conversion factor selling",blank=True, null=True)
    xcfpck = models.DecimalField(max_digits=20, decimal_places=4, default=0.00,
                                 verbose_name="Conversion factor Packaging", blank=True, null=True)
    xcfiss = models.DecimalField(max_digits=20, decimal_places=4, default=0.00, verbose_name="Conversion factor Issue",blank=True, null=True)
    # Pricing
    xpurprice = models.DecimalField(max_digits=20, decimal_places=4, default=0.00, verbose_name="Purchase Price",blank=True, null=True)
    xselprice = models.DecimalField(max_digits=20, decimal_places=4, default=0.00, verbose_name="Sales Price",blank=True, null=True)

    # Inventory
    current_stock = models.DecimalField(max_digits=20, decimal_places=4, default=0.00, verbose_name="Current Stock",blank=True, null=True)
    reorder_level = models.DecimalField(max_digits=20, decimal_places=4, default=0.00, verbose_name="Reorder Level",blank=True, null=True)
    max_stock = models.DecimalField(max_digits=20, decimal_places=4, default=0.00, verbose_name="Maximum Stock",blank=True, null=True)

    # Optional ERP fields
    manufacture_date = models.DateField(blank=True, null=True)
    shelf_location = models.CharField(max_length=100, blank=True, null=True)
    ledger_no = models.CharField(max_length=50, blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True, verbose_name="Active",blank=True, null=True)

    class Meta:
        db_table = 'item_master'
        verbose_name = 'Item Master'
        verbose_name_plural = 'Item Masters'

    def __str__(self):
        return f"{self.xitem}, {self.xname}"

