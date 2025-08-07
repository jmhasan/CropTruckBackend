import logging
from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from inventory.serializers import CurrentStockSerializer, ImtorSerializer
from utils.customlist import CustomListAPIView
logger = logging.getLogger(__name__)
from inventory.models import Imtrn, Stock, Imtor
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


class CurrentStock(APIView):
    def get(self, request, *args, **kwargs):
        token_no = self.request.query_params.get('token_no')
        xmobile = self.request.query_params.get('xmobile')
        xpocket = self.request.query_params.get('xpocket')
        snippets = Stock.objects.filter(Q(token_no=token_no) | Q(xmobile=xmobile) | Q(xpocket=xpocket))
        serializer = CurrentStockSerializer(snippets, many=True)

        return APIResponse.success(
            data=serializer.data,
            message="Stock Status retrieved successfully"
        )

class TransferEntry(APIView):
    def get(self, request, format=None):
        """Get all transfer orders for the user's business"""
        try:
            business = CompanyProfile.objects.get(pk=request.user.business_id)
        except (CompanyProfile.DoesNotExist, AttributeError):
            return APIResponse.error(
                message="User business profile not found",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Filter by business_id for security
        snippets = Imtor.objects.filter(business_id=business)
        serializer = ImtorSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """Create a new transfer order with stock entries"""
        serializer = ImtorSerializer(data=request.data)
        # get_current_stock()

        # Get user's business
        try:
            business = CompanyProfile.objects.get(pk=request.user.business_id)
        except CompanyProfile.DoesNotExist:
            return APIResponse.error(
                message="User business profile not found",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except AttributeError:
            return APIResponse.error(
                message="User does not have business_id attribute",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Extract validated data
        validated_data = serializer.validated_data
        token_no = validated_data.get('token_no')
        xunit = validated_data.get('xfunit')  # From Unit
        xfloor = validated_data.get('xffloor')  # From Floor
        xpocket = validated_data.get('xfpocket')  # From Pocket
        number_of_sacks = validated_data.get('number_of_sacks')
        # print(token_no)
        # print(xunit)
        # print(xfloor)
        # print(xpocket)
        # print(number_of_sacks)

        # ✅ Check current stock
        stock_obj = Stock.objects.filter(token_no=token_no,xunit=xunit,xfloor=xfloor,xpocket=xpocket).first()
        current_stock = stock_obj.number_of_sacks if stock_obj and stock_obj.number_of_sacks is not None else 0

        if current_stock < number_of_sacks:
            return APIResponse.error(
                message=f"Insufficient stock: Available={current_stock}, Requested={number_of_sacks}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Use transaction to ensure data consistency
        try:
            with transaction.atomic():
                # Save the transfer order
                transfer_order = serializer.save(
                    business_id=business,
                    created_by=request.user,
                    updated_by=request.user,
                    xtype='TO'
                )

                # Create stock entries
                self._create_stock_entries(transfer_order, business, request.user)

                return APIResponse.created(
                    data=serializer.data,
                    message="Transfer Order Create successfully")

        except Exception as e:
            return APIResponse.error(
                message=f"Failed to create transfer order: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _create_stock_entries(self, transfer_order, business, user):
        """Create stock transaction entries for the transfer"""
        current_datetime = datetime.now()
        # Use the full datetime instead of just time string
        xtime = current_datetime
        stock_entries = []

        # OUT entry (from source location) - Negative quantity
        out_entry = Imtrn(
            business_id=business,
            xunit=transfer_order.xfunit,
            xfloor=transfer_order.xffloor,
            xpocket=transfer_order.xfpocket,
            # xitem=transfer_order.xitem,  # You'll need to add item field to Imtor or get it another way
            xdate=current_datetime.date(),  # Use date() for date field
            xyear=current_datetime.year,
            xper=self._calculate_period(current_datetime),
            xqty=transfer_order.number_of_sacks,  # Negative for outgoing
            xval=0,  # You might want to calculate value
            xdocnum=transfer_order.ximtor,
            token_no=transfer_order.token_no,
            xdoctype="TO",  # Transfer Order
            xaction="Transfer Out",
            xsign=-1,  # Negative sign for outgoing
            xdocrow=1,
            xtime=xtime,  # Now uses datetime instead of time string
            created_by=user,
            created_at=current_datetime,
            updated_at=current_datetime,
        )
        stock_entries.append(out_entry)

        # IN entry (to destination location) - Positive quantity
        in_entry = Imtrn(
            business_id=business,
            xunit=transfer_order.xtunit,
            xfloor=transfer_order.xtfloor,
            xpocket=transfer_order.xtpocket,
            # xitem=transfer_order.xitem,  # You'll need to add item field to Imtor or get it another way
            xdate=current_datetime.date(),  # Use date() for date field
            xyear=current_datetime.year,
            xper=self._calculate_period(current_datetime),
            xqty=transfer_order.number_of_sacks,  # Positive for incoming
            xval=0,  # You might want to calculate value
            xdocnum=transfer_order.ximtor,
            token_no=transfer_order.token_no,
            xdoctype="TO",  # Transfer Order
            xaction="Transfer In",
            xsign=1,  # Positive sign for incoming
            xdocrow=2,
            xtime=xtime,  # Now uses datetime instead of time string
            created_by=user,
            created_at=current_datetime,
            updated_at=current_datetime,
        )
        stock_entries.append(in_entry)

        # Bulk create for better performance
        Imtrn.objects.bulk_create(stock_entries)

        # Update transfer order status
        transfer_order.xstatus = 'In Progress'
        transfer_order.save()

    def _calculate_period(self, date):
        """Calculate period based on your business logic"""
        return (date.month + 6) % 12 or 12


class TransferEntryDetail(APIView):

    def get(self, request, transfer_id, format=None):
        """Get specific transfer order details"""
        try:
            business = CompanyProfile.objects.get(pk=request.user.business_id)
            transfer_order = Imtor.objects.get(
                ximtor=transfer_id,
                business_id=business
            )
        except CompanyProfile.DoesNotExist:
            return APIResponse.error(
                message="User business profile not found",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Imtor.DoesNotExist:
            return APIResponse.error(
                message="Transfer order not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = ImtorSerializer(transfer_order)
        return Response(serializer.data)

    def patch(self, request, transfer_id, format=None):
        """Update transfer order status"""
        try:
            business = CompanyProfile.objects.get(pk=request.user.business_id)
            transfer_order = Imtor.objects.get(
                ximtor=transfer_id,
                business_id=business
            )
        except (CompanyProfile.DoesNotExist, Imtor.DoesNotExist):
            return APIResponse.error(
                message="Transfer order not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Only allow status updates
        allowed_fields = ['xstatus']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = ImtorSerializer(
            transfer_order,
            data=update_data,
            partial=True
        )

        if serializer.is_valid():
            with transaction.atomic():
                serializer.save(updated_by=request.user)

                # If completing the transfer, you might want to do additional processing
                if update_data.get('xstatus') == 'Completed':
                    self._complete_transfer(transfer_order, business, request.user)

            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _complete_transfer(self, transfer_order, business, user):
        """Handle transfer completion logic"""
        # Add any additional logic needed when completing a transfer
        # For example, updating inventory counts, sending notifications, etc.
        pass
