from django.db import models
from masterdata.models import AuditModel, CompanyProfile, CustomerProfile


# Create your models here.
class Glmst(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xacc')
    business_id = models.ForeignKey('masterdata.CompanyProfile', models.DO_NOTHING)
    xacc = models.CharField(max_length=100)
    xdesc = models.CharField(max_length=100, null=True, blank=True)
    xacctype = models.CharField(max_length=100, null=True, blank=True)
    xaccusage = models.CharField(max_length=100, null=True, blank=True)
    xaccsource = models.CharField(max_length=100, null=True, blank=True)
    xaccgroup = models.CharField(max_length=100, null=True, blank=True)
    xmsttype = models.CharField(max_length=100, null=True, blank=True)
    xaccgroup1 = models.CharField(max_length=100, null=True, blank=True)
    xcashacc = models.CharField(max_length=100, null=True, blank=True)
    xcoracc = models.CharField(max_length=100, null=True, blank=True)
    xhrc1 = models.CharField(max_length=100, null=True, blank=True)
    xhrc2 = models.CharField(max_length=100, null=True, blank=True)
    xhrc3 = models.CharField(max_length=100, null=True, blank=True)
    xhrc4 = models.CharField(max_length=100, null=True, blank=True)
    xhrc5 = models.CharField(max_length=100, null=True, blank=True)
    zactive = models.BooleanField(default=True)
    xteam = models.CharField(max_length=100, null=True, blank=True)
    xmember = models.CharField(max_length=100, null=True, blank=True)
    xmanager = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey('user.CustomUser', models.DO_NOTHING, related_name='Glmst_created_by_set',
                                   blank=True, null=True)
    updated_by = models.ForeignKey('user.CustomUser', models.DO_NOTHING, related_name='Glmst_updated_by_set',
                                   blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'glmst'

    def __str__(self):
        return f"{self.xacc} - {self.xdesc}"

class Glsub(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xacc' ,'xsub')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    xacc = models.CharField(max_length=100)        # part of PK and FK to glmst
    xsub = models.CharField(max_length=100)        # part of PK
    xdesc = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, related_name='Glsub_updated_by_set',
                                   blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'glsub'

    def __str__(self):
        return f"{self.xsub} - {self.xdesc}"

class Glhrc1(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xhrc1')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    xhrc1 = models.CharField(max_length=100)
    xlong = models.CharField(max_length=1000, null=True, blank=True)
    xdesc = models.CharField(max_length=100, null=True, blank=True)

    created_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, related_name='glhrc1_updated_by_set',
                                   blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'glhrc1'

    def __str__(self):
        return f"{self.xhrc1} - {self.xdesc}"

class Glhrc2(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xhrc1', 'xhrc2')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    xhrc1 = models.CharField(max_length=100)
    xhrc2 = models.CharField(max_length=100)
    xlong = models.CharField(max_length=1000, null=True, blank=True)
    xdesc = models.CharField(max_length=100, null=True, blank=True)

    created_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, related_name='glhrc2_updated_by_set',
                                   blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'glhrc2'

    def __str__(self):
        return f"{self.xhrc2} - {self.xdesc}"

class Glhrc3(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xhrc1', 'xhrc2','xhrc3')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    xhrc1 = models.CharField(max_length=100)
    xhrc2 = models.CharField(max_length=100)
    xhrc3 = models.CharField(max_length=100)
    xlong = models.CharField(max_length=1000, null=True, blank=True)
    xdesc = models.CharField(max_length=100, null=True, blank=True)

    created_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, related_name='glhrc3_updated_by_set',
                                   blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'glhrc3'

    def __str__(self):
        return f"{self.xhrc3} - {self.xdesc}"

class Glhrc4(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xhrc1', 'xhrc2','xhrc3', 'xhrc4')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    xhrc1 = models.CharField(max_length=100)
    xhrc2 = models.CharField(max_length=100)
    xhrc3 = models.CharField(max_length=100)
    xhrc4 = models.CharField(max_length=100)
    xlong = models.CharField(max_length=1000, null=True, blank=True)
    xdesc = models.CharField(max_length=100, null=True, blank=True)

    created_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, related_name='glhrc4_updated_by_set',
                                   blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'glhrc4'

    def __str__(self):
        return f"{self.xhrc4} - {self.xdesc}"

class Glhrc5(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xhrc1', 'xhrc2','xhrc3', 'xhrc4', 'xhrc5')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    xhrc1 = models.CharField(max_length=100)
    xhrc2 = models.CharField(max_length=100)
    xhrc3 = models.CharField(max_length=100)
    xhrc4 = models.CharField(max_length=100)
    xhrc5 = models.CharField(max_length=100)
    xlong = models.CharField(max_length=1000, null=True, blank=True)
    xdesc = models.CharField(max_length=100, null=True, blank=True)

    created_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.Customuser', models.DO_NOTHING, related_name='glhrc5_updated_by_set',
                                   blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'xhrc5'

    def __str__(self):
        return f"{self.xhrc5} - {self.xdesc}"

class Glheader(models.Model):
    pk = models.CompositePrimaryKey('business_id', 'xvoucher')
    business_id = models.ForeignKey('masterdata.CompanyProfile', on_delete=models.DO_NOTHING)
    xvoucher = models.CharField(max_length=100)
    xref = models.CharField(max_length=100, null=True, blank=True)
    xdate = models.DateField(null=True, blank=True)
    xlong = models.CharField(max_length=1000, null=True, blank=True)
    xpostflag = models.CharField(max_length=100, null=True, blank=True)
    xyear = models.IntegerField(null=True, blank=True)
    xper = models.IntegerField(null=True, blank=True)
    xstatusjv = models.CharField(max_length=100, null=True, blank=True)
    xdatedue = models.DateField(null=True, blank=True)
    xdesc01 = models.CharField(max_length=100, null=True, blank=True)
    xdesc02 = models.CharField(max_length=100, null=True, blank=True)
    xdesc03 = models.CharField(max_length=100, null=True, blank=True)
    xdesc04 = models.CharField(max_length=100, null=True, blank=True)
    xdesc05 = models.CharField(max_length=100, null=True, blank=True)
    xictrnno = models.CharField(max_length=100, null=True, blank=True)
    xaccdr = models.CharField(max_length=100, null=True, blank=True)
    xsubdr = models.CharField(max_length=100, null=True, blank=True)
    xnumofper = models.IntegerField(null=True, blank=True)
    xcheque = models.CharField(max_length=100, null=True, blank=True)
    xpaytype = models.CharField(max_length=100, null=True, blank=True)
    xstatus = models.CharField(max_length=100, null=True, blank=True)
    xtrngl = models.CharField(max_length=4, null=True, blank=True)
    xnote = models.CharField(max_length=250, null=True, blank=True)
    xemp = models.CharField(max_length=100, null=True, blank=True)
    xaction = models.CharField(max_length=100, null=True, blank=True)
    xproj = models.CharField(max_length=100, null=True, blank=True)

    checked_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING,related_name='glheader_checked_by_set', blank=True, null=True)
    posted_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING,related_name='glheader_posted_by_set', blank=True, null=True)
    checked_at = models.DateTimeField(blank=True, null=True)
    posted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING, related_name='glheader_created_by_set', blank=True, null=True)
    updated_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING, related_name='glheader_updated_by_set', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = 'glheader'
        managed = False
        verbose_name = 'GL Header'
        verbose_name_plural = 'GL Headers'

    def __str__(self):
        return f"{self.xvoucher} ({self.business_id})"

class Gldetail(models.Model):
    pk = models.CompositePrimaryKey('business_id', 'xvoucher', 'xrow')
    business_id = models.ForeignKey('masterdata.CompanyProfile', on_delete=models.DO_NOTHING)
    xvoucher = models.CharField(max_length=100)
    xrow = models.IntegerField()
    xacc = models.CharField(max_length=100, null=True, blank=True)
    xaccusage = models.CharField(max_length=100, null=True, blank=True)
    xaccsource = models.CharField(max_length=100, null=True, blank=True)
    xsub = models.CharField(max_length=100, null=True, blank=True)
    xdiv = models.CharField(max_length=100, null=True, blank=True)
    xsec = models.CharField(max_length=100, null=True, blank=True)
    xproj = models.CharField(max_length=100, null=True, blank=True)
    xcur = models.CharField(max_length=100, null=True, blank=True)
    xexch = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    xprime = models.DecimalField(max_digits=30, decimal_places=6, null=True, blank=True)
    xbase = models.DecimalField(max_digits=30, decimal_places=6, null=True, blank=True)
    xlong = models.CharField(max_length=1000, null=True, blank=True)
    xicacc = models.CharField(max_length=100, null=True, blank=True)
    xicsub = models.CharField(max_length=100, null=True, blank=True)
    xacctype = models.CharField(max_length=100, null=True, blank=True)
    xstatusrfp = models.CharField(max_length=100, null=True, blank=True)
    xicdiv = models.CharField(max_length=100, null=True, blank=True)
    xicsec = models.CharField(max_length=100, null=True, blank=True)
    xicproj = models.CharField(max_length=100, null=True, blank=True)
    xvmcode = models.CharField(max_length=100, null=True, blank=True)
    xamount = models.DecimalField(max_digits=30, decimal_places=6, null=True, blank=True)
    xrem = models.CharField(max_length=250, null=True, blank=True)
    xallocation = models.DecimalField(max_digits=30, decimal_places=6, null=True, blank=True)
    xcheque = models.CharField(max_length=100, null=True, blank=True)
    xpaytype = models.CharField(max_length=100, null=True, blank=True)
    xstatus = models.CharField(max_length=100, null=True, blank=True)
    xtypegl = models.CharField(max_length=100, null=True, blank=True)
    xinvnum = models.CharField(max_length=100, null=True, blank=True)
    xref = models.CharField(max_length=100, null=True, blank=True)
    xoriginal = models.CharField(max_length=100, null=True, blank=True)
    xdateapp = models.DateTimeField(null=True, blank=True)
    xpaycode = models.CharField(max_length=100, null=True, blank=True)
    xexchval = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    xdateclr = models.DateTimeField(null=True, blank=True)
    xflag = models.CharField(max_length=100, null=True, blank=True)
    xdatedue = models.DateTimeField(null=True, blank=True)
    glheader = models.ForeignObject(
        to='Glheader',
        from_fields=('business_id', 'xvoucher'),
        to_fields=('business_id', 'xvoucher'),
        on_delete=models.DO_NOTHING,   # matches ON UPDATE/DELETE NO ACTION behavior
        related_name='gldetails_header'
    )
    glmst = models.ForeignObject(
        to='Glmst',
        from_fields=('business_id', 'xacc'),
        to_fields=('business_id', 'xacc'),
        on_delete=models.DO_NOTHING,
        related_name='gldetails_glmst',
        null=True
    )

    created_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING,
                                   related_name='gldetail_created_by_set', blank=True, null=True)
    updated_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING,
                                   related_name='gldetail_updated_by_set', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gldetail'
        verbose_name = 'GL Detail'
        verbose_name_plural = 'GL Details'

    def __str__(self):
        return f"{self.xvoucher}-{self.xrow}"


# LOAN_STATUS = [
#     ('PENDING', 'Pending'),
#     ('APPROVED', 'Approved'),
#     ('DISBURSED', 'Disbursed'),
#     ('ACTIVE', 'Active'),
#     ('DELINQUENT', 'Delinquent'),
#     ('PAID_OFF', 'Paid Off'),
#     ('DEFAULTED', 'Defaulted'),
#     ('CANCELLED', 'Cancelled'),
# ]
#
# LOAN_TYPES = [
#     ('CROP', 'Crop Loan'),
#     ('EQUIPMENT', 'Equipment Loan'),
#     ('OPERATIONAL', 'Operational Loan'),
#     ('EMERGENCY', 'Emergency Loan'),
#     ('OTHER', 'Other'),
# ]
#
# PAYMENT_TYPES = [
#     ('PRINCIPAL', 'Principal'),
#     ('INTEREST', 'Interest'),
#     ('PENALTY', 'Penalty'),
#     ('FEES', 'Fees'),
# ]
#
# PAYMENT_METHODS = [
#     ('CASH', 'Cash'),
#     ('BANK_TRANSFER', 'Bank Transfer'),
#     ('CHECK', 'Check'),
#     ('CROP_SALE', 'Crop Sale Deduction'),
# ]
#
#
# class Loan(AuditModel):
#     pk = models.CompositePrimaryKey('business_id', 'xtrnnum')
#     business_id = models.ForeignKey('masterdata.CompanyProfile', on_delete=models.DO_NOTHING)
#     xtrnnum = models.CharField(max_length=50)
#     xref = models.ForeignKey(CustomerProfile, on_delete=models.DO_NOTHING)
#     xyear = models.IntegerField(null=True, blank=True)
#     xper = models.IntegerField(null=True, blank=True)
#     xtype = models.CharField(max_length=100)
#     loan_type = models.CharField(max_length=100, choices = LOAN_TYPES)
#     disbursement_date = models.DateField(null=True, blank=True)
#     maturity_date = models.DateField(null=True, blank=True)
#     interest_date = models.DateField(null=True, blank=True)
#     certificate_no = models.CharField(max_length=20, blank=True, null=True)
#     xamount = models.DecimalField(max_digits=30, decimal_places=6,default= 0.0)
#     interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
#     payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
#     payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
#     xstatus = models.CharField(max_length=50, choices = LOAN_STATUS)
#     xnote = models.CharField(max_length = 250, blank=True, null=True)
#     xvoucher = models.CharField(max_length = 100, blank=True, null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'glloan'
#         verbose_name = 'GL Loan'
#         verbose_name_plural = 'GL Loans'
#
#     def __str__(self):
#         return f"{self.xtrnnum}"