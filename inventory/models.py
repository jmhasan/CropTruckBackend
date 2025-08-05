from django.db import models

from masterdata.models import AuditModel, CompanyProfile


# Create your models here.
class Imtrn(models.Model):
    pk = models.CompositePrimaryKey('business_id_id', 'xdocnum', 'xdocrow', 'xsign')
    business_id = models.ForeignKey('masterdata.CompanyProfile', on_delete=models.DO_NOTHING)
    xdocnum = models.CharField(max_length=100)
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

