import logging
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
logger = logging.getLogger(__name__)
from inventory.models import Imtrn
from masterdata.models import CompanyProfile
from ops.models import Certificate, CertificateDetails
from utils.response import APIResponse

class CertificatePost(APIView):
    """
    Post stock entries from certificate and certificate_details into imtrn table
    """

    def post(self, request, token_no):
        try:
            # 1️⃣ Get and validate business
            try:
                business = CompanyProfile.objects.get(pk=request.user.business_id)
            except CompanyProfile.DoesNotExist:
                return Response({
                    'success': False,
                    'message': "User business profile not found"
                }, status=status.HTTP_400_BAD_REQUEST)

            # 2️⃣ Get and validate certificate (parent)
            try:
                certificate = Certificate.objects.get(token_no=token_no, business_id=business)
            except Certificate.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Certificate {token_no} not found for your business'
                }, status=status.HTTP_404_NOT_FOUND)

            # 3️⃣ Check if certificate has already been posted
            if certificate.xstatus == "Posted":
                return Response({
                    'success': False,
                    'message': f'Certificate {token_no} has already been posted to stock'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 4️⃣ Validate certificate status (adjust valid statuses as needed)
            valid_statuses = ['Open', 'Ready', 'Loaded']  # Define your valid statuses
            if hasattr(certificate, 'xstatus') and certificate.xstatus not in valid_statuses:
                return Response({
                    'success': False,
                    'message': f'Certificate status "{certificate.xstatus}" cannot be posted to stock'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 5️⃣ Get certificate details (child items)
            certificate_details = CertificateDetails.objects.filter(
                token_no=token_no,
                business_id=business
            ).select_related()  # Add select_related if there are foreign keys

            if not certificate_details.exists():
                return Response({
                    'success': False,
                    'message': 'No certificate details found for posting to stock'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 6️⃣ Prepare common values
            entry_date = certificate.created_at.date() if certificate.created_at else timezone.now().date()
            current_time = timezone.now().time()
            xtime = datetime.combine(entry_date, current_time)
            current_datetime = timezone.now()

            # 7️⃣ Process transaction
            with transaction.atomic():
                imtrn_entries = []

                # Prepare bulk create data
                for idx, detail in enumerate(certificate_details, 1):
                    # Validate detail data (add more validations as needed)
                    if not detail.xitem:
                        logger.warning(f"Certificate detail {detail.id} missing xitem, skipping")
                        continue

                    if not detail.number_of_sacks or detail.number_of_sacks <= 0:
                        logger.warning(f"Certificate detail {detail.id} has invalid quantity, skipping")
                        continue

                    # Create Imtrn entry data
                    imtrn_entry = Imtrn(
                        business_id=business,
                        xunit=detail.xunit,
                        xfloor=detail.xfloor,
                        xpocket=detail.xpocket,
                        xitem=detail.xitem,
                        xwh=getattr(certificate, 'xwh', None),  # Safe attribute access
                        xdate=current_datetime,
                        xyear=current_datetime.year,
                        xper=(current_datetime.month + 6) % 12 or 12,
                        xqty=detail.number_of_sacks,  # or convert to weight if needed
                        xval=detail.total_rent or 0,  # map to valuation if needed
                        xdocnum=token_no,
                        xdoctype="ADRE",
                        xaction="Receipt",
                        xsign=1,
                        xdocrow=idx,
                        xtime=xtime,
                        created_by=request.user,
                        created_at=current_datetime,  # Add if your model has this field
                        updated_at=current_datetime,  # Add if your model has this field
                    )
                    imtrn_entries.append(imtrn_entry)

                # Check if we have valid entries to create
                if not imtrn_entries:
                    return Response({
                        'success': False,
                        'message': 'No valid certificate details found for posting to stock'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Bulk create stock transactions
                created_entries = Imtrn.objects.bulk_create(imtrn_entries)

                # Update certificate status
                certificate.xstatus = "Posted"
                certificate.posted_at = current_datetime  # Add if your model has this field
                certificate.posted_by = request.user.id  # Add if your model has this field
                certificate.save()

                # Log successful operation
                logger.info(
                    f"Certificate {token_no} successfully posted to stock. "
                    f"Created {len(created_entries)} entries. User: {request.user.id}"
                )

            # 8️⃣ Success response
            return Response({
                'success': True,
                'message': f'Successfully posted {len(created_entries)} stock entries from certificate {token_no}',
                'data': {
                    'certificate_token': token_no,
                    'created_count': len(created_entries),
                    'posted_at': current_datetime.isoformat(),
                    'entries': [
                        {
                            'xdocnum': entry.xdocnum,
                            'xdocrow': entry.xdocrow,
                            'xitem': entry.xitem,
                            'xqty': entry.xqty
                        } for entry in created_entries
                    ]
                }
            }, status=status.HTTP_201_CREATED)

        except Certificate.DoesNotExist:
            logger.error(f"Certificate {token_no} not found for business {request.user.business_id}")
            return Response({
                'success': False,
                'message': f'Certificate {token_no} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(
                f"Failed to post certificate {token_no} to stock: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': request.user.id,
                    'business_id': request.user.business_id,
                    'token_no': token_no
                }
            )
            return Response({
                'success': False,
                'message': 'Failed to post certificate to stock. Please try again or contact support.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)