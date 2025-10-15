from datetime import date
from django.db import models, transaction

from masterdata.models import AuditModel, CompanyProfile


# Create your models here.
class Imtrn(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xdocnum', 'xdocrow', 'xsign')
    business_id = models.ForeignKey('masterdata.CompanyProfile', on_delete=models.DO_NOTHING)
    xdocnum = models.CharField(max_length=100)
    token_no = models.CharField(max_length=10)
    xdocrow = models.IntegerField()
    xsign = models.IntegerField()
    xaction = models.CharField(max_length=100, blank=True, null=True)
    xitem = models.CharField(max_length=100, blank=True, null=True)
    xwh = models.CharField(max_length=100, blank=True, null=True)
    xdate = models.DateTimeField(blank=True, null=True)
    xyear = models.IntegerField(blank=True, null=True)
    xper = models.IntegerField(blank=True, null=True)
    xqty = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    xval = models.DecimalField(max_digits=30, decimal_places=6, blank=True, null=True)
    xvalpost = models.DecimalField(max_digits=30, decimal_places=6, blank=True, null=True)
    xnote = models.CharField(max_length=250, blank=True, null=True)
    xdoctype = models.CharField(max_length=100, blank=True, null=True)
    xproj = models.CharField(max_length=100, blank=True, null=True)
    xunit = models.CharField(max_length=100, blank=True, null=True)
    xfloor = models.CharField(max_length=100, blank=True, null=True)
    xpocket = models.CharField(max_length=100, blank=True, null=True)
    xbatch = models.CharField(max_length=100, blank=True, null=True)
    xtime = models.DateTimeField(blank=True, null=True)
    xtrnim = models.CharField(max_length=10, blank=True, null=True)
    xbin = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('user.CustomUser', on_delete=models.DO_NOTHING,
                                   related_name='imtrn_updated_by_set', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'imtrn'

class Stock(models.Model):
    token_no = models.CharField(max_length=10, primary_key=True)
    customer_code = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    xmobile = models.CharField(max_length=20, blank=True, null=True)
    xunit = models.CharField(max_length=100, blank=True, null=True)
    xfloor = models.CharField(max_length=100, blank=True, null=True)
    xpocket = models.CharField(max_length=100, blank=True, null=True)
    number_of_sacks = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'stock'


class Imtor(AuditModel):
    @staticmethod
    def generate_transfer_number():
        """Generate unique transfer order number with format TO-YY-XXXXXX"""
        with transaction.atomic():
            year_str = date.today().strftime('%y')
            prefix = f"TO-{year_str}-"

            # Use select_for_update to prevent race conditions
            last_entry = (Imtor.objects
                          .filter(ximtor__startswith=prefix)
                          .select_for_update()
                          .order_by('-ximtor')
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

    pk = models.CompositePrimaryKey('business_id_id', 'ximtor')
    business_id = models.ForeignKey(CompanyProfile, on_delete=models.DO_NOTHING)
    ximtor = models.CharField(max_length=100, default=generate_transfer_number)
    token_no = models.CharField(max_length=10)
    xtype = models.CharField(max_length=100)
    # From Location
    xfunit = models.CharField(max_length=100, blank=True, null=True)
    xffloor = models.CharField(max_length=100, blank=True, null=True)
    xfpocket = models.CharField(max_length=100, blank=True, null=True)
    # To Locations
    xtunit = models.CharField(max_length=100, blank=True, null=True)
    xtfloor = models.CharField(max_length=100, blank=True, null=True)
    xtpocket = models.CharField(max_length=100, blank=True, null=True)
    number_of_sacks = models.IntegerField()
    xstatus = models.CharField(max_length=100, default='Open', blank=True ,null = True )

    class Meta:
        db_table = 'imtor'
        verbose_name = 'Transfer Order'
        verbose_name_plural = 'Transfer Orders'