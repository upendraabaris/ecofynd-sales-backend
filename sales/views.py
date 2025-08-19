from django.shortcuts import render

# Create your views here.

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import SalesData
from .serializers import SalesDataSerializer
from django.db.models import Q


@api_view(['GET'])
def top_profit_products(request):
    products = sorted(
    SalesData.objects.all(),
    key=lambda x: x.profit()['profit_amount'] if x.profit() else Decimal('-999999'),
    reverse=True
)[:5]
    serializer = SalesDataSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def top_loss_products(request):
    products = sorted(SalesData.objects.all(), key=lambda x: x.profit())[:5]
    serializer = SalesDataSerializer(products, many=True)
    return Response(serializer.data)

from rest_framework.views import APIView
from rest_framework.response import Response
from decimal import Decimal
from django.db.models import Sum
from .models import SalesData
from django.db.models.functions import Lower

from datetime import datetime,timedelta
from rest_framework.exceptions import ValidationError

from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

class TopProfitableProductsAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        qs = SalesData.objects.exclude(status__iexact='Rto').exclude(status__iexact='Returned')

        start, end = None, None
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                qs = qs.filter(order_date__date__gte=start, order_date__date__lte=end)
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

        # ---------- helper for aggregation ----------
        def aggregate_data(qs):
            data = (
                qs.values('skucode')
                .annotate(
                    total_vendor_transfer=Sum('vendor_transfer'),
                    total_selling_price=Sum('selling_price'),
                    total_units=Sum('units_sold'),
                    total_actual_price=Sum('actual_product_price'),
                    total_collected_amount=Sum('collected_amount'),
                )
            )
            total_units_sold = 0
            total_vendor_transfer_all = Decimal('0.00')
            total_collected_amount_all = Decimal('0.00')
            profitable_products = []

            for item in data:
                sku = item['skucode']
                vendor_transfer = item['total_vendor_transfer'] or Decimal('0.00')
                selling_price = item['total_selling_price'] or Decimal('0.00')
                overhead = selling_price * Decimal('0.10')
                units = item['total_units'] or 0
                collected_amount = item['total_collected_amount'] or Decimal('0.00')
                actual_price = item['total_actual_price'] or Decimal('0.00')
                total_cost = actual_price
                profit_amount = vendor_transfer - (total_cost + overhead)
                profit_percent = (profit_amount / selling_price) * 100 if selling_price > 0 else Decimal('0.00')

                if profit_amount > 0:
                    total_units_sold += units
                    total_vendor_transfer_all += vendor_transfer
                    total_collected_amount_all += collected_amount
                    profitable_products.append({
                        "sku": sku,
                        "vendor_transfer": round(vendor_transfer, 2),
                        "total_selling_price": round(selling_price, 2),
                        "units": units,
                        "collected_amount": round(collected_amount, 2),
                        "overhead": round(overhead, 2),
                        "total_cost": round(total_cost, 2),
                        "profit_amount": round(profit_amount, 2),
                        "profit_percent": round(profit_percent, 2)
                    })

            return {
                "top_profitable_products": sorted(profitable_products, key=lambda x: x['profit_amount'], reverse=True)[:],
                "total_units_sold": total_units_sold,
                "total_vendor_transfer": round(total_vendor_transfer_all, 2),
                "total_profitable_count": len(profitable_products),
                "total_collected_amount": round(total_collected_amount_all, 2)
            }

        # ---------- current period ----------
        current_data = aggregate_data(qs)

        # ---------- previous period ----------
        previous_data = {}
        if start and end:
            delta_days = (end - start).days + 1
            prev_end = start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=delta_days - 1)
            qs_prev = SalesData.objects.exclude(status__iexact='Rto').exclude(status__iexact='Returned') \
                .filter(order_date__date__gte=prev_start, order_date__date__lte=prev_end)
            previous_data = aggregate_data(qs_prev)

        # ---------- comparison ----------
        comparison = {}
        if previous_data:
            for key in ["total_units_sold", "total_vendor_transfer", "total_profitable_count", "total_collected_amount"]:
                curr = Decimal(current_data[key])
                prev = Decimal(previous_data[key])
                if prev != 0:
                    percent_change = ((curr - prev) / prev) * 100
                else:
                    percent_change = Decimal('0.00') if curr == 0 else Decimal('100.00')

                if curr > prev:
                    status = "increase"
                elif curr < prev:
                    status = "decrease"
                else:
                    status = "no change"

                comparison[key] = {
                    "current": float(round(curr, 2)),
                    "previous": float(round(prev, 2)),
                    "percent_change": float(round(percent_change, 2)),
                    "status": status
                }

        return Response({
            **current_data,
            "previous_period": previous_data,
            "comparison": comparison
        })



# class TopProfitableProductsAPIView(APIView):
#     def get(self, request):
#         start_date_str = request.query_params.get("start_date")
#         end_date_str = request.query_params.get("end_date")

#         if not start_date_str or not end_date_str:
#             raise ValidationError("start_date and end_date are required.")

#         try:
#             start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#             end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
#         except ValueError:
#             raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

#         # Calculate previous period dates
#         period_days = (end_date - start_date).days + 1
#         prev_end_date = start_date - timedelta(days=1)
#         prev_start_date = prev_end_date - timedelta(days=period_days - 1)

#         # Get data for both periods
#         current_period_data = self.get_period_data(start_date, end_date)
#         previous_period_data = self.get_period_data(prev_start_date, prev_end_date)

#         return Response({
#             "current_period": current_period_data,
#             "previous_period": previous_period_data,
#             "period_days": period_days
#         })

#     def get_period_data(self, start_date, end_date):
#         qs = SalesData.objects.exclude(status__iexact='Rto').exclude(status__iexact='Returned')
#         qs = qs.filter(order_date__date__gte=start_date, order_date__date__lte=end_date)

#         data = (
#             qs.values('skucode')
#             .annotate(
#                 total_vendor_transfer=Sum('vendor_transfer'),
#                 total_selling_price=Sum('selling_price'),
#                 total_units=Sum('units_sold'),
#                 total_actual_price=Sum('actual_product_price'),
#                 total_collected_amount=Sum('collected_amount'),
#             )
#         )

#         total_units_sold = 0
#         total_vendor_transfer_all = Decimal('0.00')
#         total_collected_amount_all = Decimal('0.00')
#         profitable_products = []

#         for item in data:
#             sku = item['skucode']
#             vendor_transfer = item['total_vendor_transfer'] or Decimal('0.00')
#             selling_price = item['total_selling_price'] or Decimal('0.00')
#             overhead = selling_price * Decimal('0.10')
#             units = item['total_units'] or 0
#             collected_amount = item['total_collected_amount'] or Decimal('0.00')
#             actual_price = item['total_actual_price'] or Decimal('0.00')
#             total_cost = actual_price
#             profit_amount = vendor_transfer - (total_cost + overhead)
#             profit_percent = (profit_amount / selling_price) * 100 if selling_price > 0 else Decimal('0.00')

#             if profit_amount > 0:
#                 total_units_sold += units
#                 total_vendor_transfer_all += vendor_transfer
#                 total_collected_amount_all += collected_amount
#                 profitable_products.append({
#                     "sku": sku,
#                     "vendor_transfer": round(vendor_transfer, 2),
#                     "total_selling_price": round(selling_price, 2),
#                     "units": units,
#                     "collected_amount": round(collected_amount, 2),
#                     "overhead": round(overhead, 2),
#                     "total_cost": round(total_cost, 2),
#                     "profit_amount": round(profit_amount, 2),
#                     "profit_percent": round(profit_percent, 2)
#                 })

#         top_5 = sorted(profitable_products, key=lambda x: x['profit_amount'], reverse=True)

#         return {
#             "top_profitable_products": top_5,
#             "total_units_sold": total_units_sold,
#             "total_vendor_transfer": round(total_vendor_transfer_all, 2),
#             "total_profitable_count": len(profitable_products),
#             "total_collected_amount": round(total_collected_amount_all, 2)
#         }


from django.db.models import Sum, DecimalField, Case, When, F
class TopLossProductsAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        # RTO and Returned orders ko exclude karo
        qs = SalesData.objects.exclude(status__iexact='Rto')
from django.db.models import Sum, Case, When, F, DecimalField
from decimal import Decimal
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError


class TopLossProductsAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        # Base queryset (exclude RTO)
        qs = SalesData.objects.exclude(status__iexact='Rto')

        if not (start_date and end_date):
            raise ValidationError("Both start_date and end_date are required")

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

        # Current period queryset
        current_qs = qs.filter(order_date__date__gte=start, order_date__date__lte=end)

        # Previous period range (same length as current period, just before start_date)
        period_days = (end - start).days + 1
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_days - 1)

        previous_qs = qs.filter(order_date__date__gte=prev_start, order_date__date__lte=prev_end)

        def aggregate_loss(qset):
            data = (
                qset.values('skucode')
                .annotate(
                    total_vendor_transfer=Sum('vendor_transfer'),
                    total_selling_price=Sum(
                        Case(
                            When(selling_price__lt=0, then=F('selling_price') * -1),
                            default=F('selling_price'),
                            output_field=DecimalField(),
                        )
                    ),
                    total_units=Sum('units_sold'),
                    total_actual_price=Sum('actual_product_price'),
                    total_collected_amount=Sum(
                        Case(
                            When(selling_price__lt=0, then=F('collected_amount') * -1),
                            default=F('collected_amount'),
                            output_field=DecimalField(),
                        )
                    ),
                )
            )

            total_units_sold = 0
            total_vendor_transfer_all = Decimal('0.00')
            total_collected_amount_all = Decimal('0.00')
            loss_products = []

            for item in data:
                sku = item['skucode']
                vendor_transfer = item['total_vendor_transfer'] or Decimal('0.00')
                selling_price = item['total_selling_price'] or Decimal('0.00')
                overhead = selling_price * Decimal('0.10')
                units = item['total_units'] or 0
                collected_amount = item['total_collected_amount'] or Decimal('0.00')
                actual_price = item['total_actual_price'] or Decimal('0.00')

                total_cost = actual_price
                profit_amount = vendor_transfer - (total_cost + overhead)
                profit_percent = (profit_amount / selling_price) * 100 if selling_price > 0 else Decimal('0.00')

                if profit_amount < 0:
                    total_units_sold += units
                    total_vendor_transfer_all += vendor_transfer
                    total_collected_amount_all += collected_amount
                    loss_products.append({
                        "sku": sku,
                        "vendor_transfer": round(vendor_transfer, 2),
                        "total_selling_price": round(selling_price, 2),
                        "units": units,
                        "collected_amount": round(collected_amount, 2),
                        "overhead": round(overhead, 2),
                        "total_cost": round(total_cost, 2),
                        "profit_amount": round(profit_amount, 2),
                        "profit_percent": round(profit_percent, 2)
                    })

            return {
                "products": loss_products,
                "total_units_sold": total_units_sold,
                "total_vendor_transfer": round(total_vendor_transfer_all, 2),
                "total_loss_count": len(loss_products),
                "total_collected_amount": round(total_collected_amount_all, 2),
            }

        # Current & Previous aggregation
        current_data = aggregate_loss(current_qs)
        previous_data = aggregate_loss(previous_qs)

        # Comparison helper
        def compare(current, previous):
            if previous == 0:
                return {"current": current, "previous": previous, "percent_change": 100.0 if current > 0 else 0.0,
                        "status": "increase" if current > 0 else "no change"}
            percent_change = ((current - previous) / previous) * 100
            if current > previous:
                status = "increase"
            elif current < previous:
                status = "decrease"
            else:
                status = "no change"
            return {
                "current": float(current),
                "previous": float(previous),
                "percent_change": round(percent_change, 2),
                "status": status
            }

        comparison = {
            "total_units_sold": compare(current_data["total_units_sold"], previous_data["total_units_sold"]),
            "total_vendor_transfer": compare(current_data["total_vendor_transfer"], previous_data["total_vendor_transfer"]),
            "total_loss_count": compare(current_data["total_loss_count"], previous_data["total_loss_count"]),
            "total_collected_amount": compare(current_data["total_collected_amount"], previous_data["total_collected_amount"]),
        }

        return Response({
            "top_loss_making_products": current_data["products"],
            "total_units_sold": current_data["total_units_sold"],
            "total_vendor_transfer": current_data["total_vendor_transfer"],
            "total_loss_count": current_data["total_loss_count"],
            "total_collected_amount": current_data["total_collected_amount"],
            "previous_period": previous_data,
            "comparison": comparison
        })

        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                qs = qs.filter(order_date__date__gte=start, order_date__date__lte=end)
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

        # SKU-wise aggregation
        data = (
            qs.values('skucode')
            .annotate(
                total_vendor_transfer=Sum('vendor_transfer'),
                total_selling_price=Sum(
                    Case(
                    When(selling_price__lt=0, then=F('selling_price') * -1),
                    default=F('selling_price'),
                    output_field=DecimalField(),
                    )
                ),
                total_units=Sum('units_sold'),
                total_actual_price=Sum('actual_product_price'),
                # total_collected_amount=Sum('collected_amount'),
                total_collected_amount=Sum(
                    Case(
                    When(selling_price__lt=0, then=F('collected_amount') * -1),
                    default=F('collected_amount'),
                    output_field=DecimalField(),
                    )
                ),
            )
        )

        total_units_sold = 0
        total_vendor_transfer_all = Decimal('0.00')
        total_collected_amount_all = Decimal('0.00')
        loss_products = []

        for item in data:
            sku = item['skucode']
            vendor_transfer = item['total_vendor_transfer'] or Decimal('0.00')
            selling_price = item['total_selling_price'] or Decimal('0.00')
            overhead = selling_price * Decimal('0.10')
            units = item['total_units'] or 0
            collected_amount=item['total_collected_amount'] or Decimal('0.00')
            actual_price = item['total_actual_price'] or Decimal('0.00')
            
            total_cost = actual_price
            profit_amount = vendor_transfer - (total_cost + overhead)
            profit_percent = (profit_amount / selling_price) * 100 if selling_price > 0 else Decimal('0.00')
            

            if profit_amount < 0:
                total_units_sold += units
                total_vendor_transfer_all += vendor_transfer
                total_collected_amount_all += collected_amount 
                loss_products.append({
                        "sku": sku,
                        "vendor_transfer": round(vendor_transfer, 2),
                        "total_selling_price": round(selling_price, 2),
                        "units":units,
                        "collected_amount": round(collected_amount,2),
                        "overhead": round(overhead, 2),
                        "total_cost": round(total_cost, 2),
                        "profit_amount": round(profit_amount, 2),
                        "profit_percent": round(profit_percent, 2)
                })

        # Top 5 by lowest profit_amount (highest loss)
        top_5_loss = sorted(loss_products, key=lambda x: x['profit_amount'])[:]
        total_loss_count = len(loss_products)
        # return Response({"top_loss_making_products": top_5_loss})
        return Response({
            "top_loss_making_products": top_5_loss,
            "total_units_sold": total_units_sold,
            "total_vendor_transfer": round(total_vendor_transfer_all, 2),
            "total_loss_count": total_loss_count,
            "total_collected_amount": round(total_collected_amount_all,2)
        })


# class TopSellingByUnitsAPIView(APIView):
#     def get(self, request):
#         start_date = request.query_params.get("start_date")
#         end_date = request.query_params.get("end_date")

#         qs = SalesData.objects.exclude(status__iexact='Rto')

#         if start_date and end_date:
#             try:
#                 start = datetime.strptime(start_date, "%Y-%m-%d")
#                 end = datetime.strptime(end_date, "%Y-%m-%d")
#                 qs = qs.filter(order_date__date__gte=start, order_date__date__lte=end)
#             except ValueError:
#                 raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

#         data = (
#             qs.values('skucode')
#             .annotate(
#                 total_units=Sum('units_sold'),
#                 total_vendor_transfer=Sum('vendor_transfer'),
#                 total_selling_price=Sum('selling_price'),
#                 total_actual_price=Sum('actual_product_price'),
#             )
#         )

#         result = []
#         for item in data:
#             result.append({
#                 "sku": item['skucode'],
#                 "units_sold": item['total_units'] or 0,
#                 # "vendor_transfer": float(item['total_vendor_transfer'] or 0),
#                 # "selling_price": float(item['total_selling_price'] or 0),
#                 # "actual_price": float(item['total_actual_price'] or 0)
#             })

#         top_by_units = sorted(result, key=lambda x: x['units_sold'], reverse=True)[:5]

#         return Response({
#             "top_selling_by_units": top_by_units
#         })


class TopSellingByUnitsAPIView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")


        qs = SalesData.objects.all();

        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                qs = qs.filter(order_date__date__gte=start, order_date__date__lte=end)
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

        # 1. Top Selling by Units (excluding RTO)
        selling_qs = qs.exclude(status__iexact='Rto')
        selling_data = (
            selling_qs.values('skucode')
            .annotate(total_units=Sum('units_sold'))
        )

        selling_result = [
            {
                "sku": item['skucode'],
                "units_sold": item['total_units'] or 0
            }
            for item in selling_data
        ]
        top_selling_by_units = sorted(selling_result, key=lambda x: x['units_sold'], reverse=True)[:5]

        # 2. Top Returned Units (status = Returned)
        returned_qs = qs.filter(status__iexact='Returned')
        returned_data = (
            returned_qs.values('skucode')
            .annotate(returned_units=Sum("units_sold"))
        )

        returned_result = [
            {
                "sku": item['skucode'],
                "units_returned": item["returned_units"] or 0
            }
            for item in returned_data
        ]

        top_returned_units = sorted(returned_result, key=lambda x:x['units_returned'], reverse= True)[:5]

        # 3. Top RTO Units (status = RTO)
        rto_qs = qs.filter(status__iexact='Rto')
        rto_data = (
            rto_qs.values('skucode')
            .annotate(rto_units=Sum("units_sold"))
        )

        rto_result = [
            {
                "sku": item['skucode'],
                "units_rto": item["rto_units"] or 0
            }
            for item in rto_data
        ]

        top_rto_units = sorted(rto_result, key=lambda x:x['units_rto'], reverse= True)[:5]

        return Response({
            "top_selling_by_units":top_selling_by_units,
            "top_returned_units":top_returned_units,
            "top_rto_units":top_rto_units
        })

from django.db.models import Sum,Count, F
from django.db.models.functions import Abs
# class SalesSummaryAPIView(APIView):
#     def get(self,request):
#         start_date_str = request.query_params.get("start_date")
#         end_date_str = request.query_params.get("end_date")

#         if not start_date_str or not end_date_str:
#             raise ValidationError("start date and end date are required")

#         try:
#             start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#             end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
#         except ValueError:
#             raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

#         qs = SalesData.objects.filter(order_date__date__gte=start_date, order_date__date__lte=end_date)

#           # Aggregations with absolute value
        
#         total_sales = qs.aggregate(total=Sum(Abs(F("collected_amount"))))["total"] or 0

#         delivered_data = qs.filter(status__iexact="Open").aggregate(
#             total=Sum(Abs(F("collected_amount"))),
#             count=Count("id")
#         )

#         rto_data = qs.filter(status__iexact="Rto").aggregate(
#             total=Sum(Abs(F("collected_amount"))),
#             count=Count("id")
#         )

#         returned_data = qs.filter(status__iexact="Returned").aggregate(
#             total=Sum(Abs(F("collected_amount"))),
#             count=Count("id")
#         )

#         exchanged_data = qs.filter(status__iexact="Exchanged").aggregate(
#             total=Sum(Abs(F("collected_amount"))),
#             count=Count("id")
#         )

#         # Date-wise breakdown
#         daily_data = (
#             qs.values("order_date__date","skucode")
#             .annotate(
#                 daily_sales=Sum(Abs(F("collected_amount"))),
#                 daily_delivered=Sum(Abs(F("collected_amount")), filter=Q(status__iexact="Open")),
#                 daily_delivered_count=Count("id", filter=Q(status__iexact="Open")),
#                 daily_rto=Sum(Abs(F("collected_amount")), filter=Q(status__iexact="Rto")),
#                 daily_rto_count=Count("id", filter=Q(status__iexact="Rto")),
#                 daily_returned=Sum(Abs(F("collected_amount")), filter=Q(status__iexact="Returned")),
#                 daily_returned_count=Count("id", filter=Q(status__iexact="Returned")),
#                 daily_exchanged=Sum(Abs(F("collected_amount")), filter=Q(status__iexact="Exchanged")),
#                 daily_exchanged_count=Count("id", filter=Q(status__iexact="Exchanged")),
#             )
#             .order_by("order_date__date", "skucode")
#         )

#         return Response({
#             "summary": {
#                 "total_sales": total_sales,
#                 "delivered_amount": delivered_data["total"] or 0,
#                 "delivered_count": delivered_data["count"] or 0,
#                 "rto_amount": rto_data["total"] or 0,
#                 "rto_count": rto_data["count"] or 0,
#                 "returned_amount": returned_data["total"] or 0,
#                 "returned_count": returned_data["count"] or 0,
#                 "exchanged_amount": exchanged_data["total"] or 0,
#                 "exchanged_count": exchanged_data["count"] or 0,
#             },
#             "daily": list(daily_data)
#         })

from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import Abs
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

class SalesSummaryAPIView(APIView):
    def get(self, request):
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if not start_date_str or not end_date_str:
            raise ValidationError("start date and end date are required")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

        # Period length
        delta_days = (end_date - start_date).days + 1  # +1 because both inclusive
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=delta_days - 1)

        # Current period queryset
        qs_current = SalesData.objects.filter(order_date__date__gte=start_date,
                                              order_date__date__lte=end_date)
        # Previous period queryset
        qs_previous = SalesData.objects.filter(order_date__date__gte=prev_start_date,
                                               order_date__date__lte=prev_end_date)

        def aggregate_summary(qs):
            return {
                "total_sales": qs.aggregate(total=Sum(Abs(F("collected_amount"))))["total"] or 0,
                "delivered_amount": qs.filter(status__iexact="Open").aggregate(total=Sum(Abs(F("collected_amount"))))["total"] or 0,
                "delivered_count": qs.filter(status__iexact="Open").count(),
                "rto_amount": qs.filter(status__iexact="Rto").aggregate(total=Sum(Abs(F("collected_amount"))))["total"] or 0,
                "rto_count": qs.filter(status__iexact="Rto").count(),
                "returned_amount": qs.filter(status__iexact="Returned").aggregate(total=Sum(Abs(F("collected_amount"))))["total"] or 0,
                "returned_count": qs.filter(status__iexact="Returned").count(),
                "exchanged_amount": qs.filter(status__iexact="Exchanged").aggregate(total=Sum(Abs(F("collected_amount"))))["total"] or 0,
                "exchanged_count": qs.filter(status__iexact="Exchanged").count(),
            }

        # Get current and previous summaries
        current_summary = aggregate_summary(qs_current)
        previous_summary = aggregate_summary(qs_previous)

        # Calculate percentage change
        comparison_detail = {}
        for key in current_summary.keys():
            curr = Decimal(current_summary[key])
            prev = Decimal(previous_summary[key])

            if prev != 0:
                percent_change = ((curr - prev) / prev) * 100
            else:
                percent_change = Decimal('0.00') if curr == 0 else Decimal('100.00')

            if curr > prev:
                status = "increase"
            elif curr < prev:
                status = "decrease"
            else:
                status = "no change"

            comparison_detail[key] = {
                "current": round(curr, 2),
                "previous": round(prev, 2),
                "percent_change": round(percent_change, 2),
                "status": status
            }


        # Daily breakdown for current period
        daily_data = (
            qs_current.values("order_date__date", "skucode")
            .annotate(
                daily_sales=Sum(Abs(F("collected_amount"))),
                daily_delivered=Sum(Abs(F("collected_amount")), filter=Q(status__iexact="Open")),
                daily_delivered_count=Count("id", filter=Q(status__iexact="Open")),
                daily_rto=Sum(Abs(F("collected_amount")), filter=Q(status__iexact="Rto")),
                daily_rto_count=Count("id", filter=Q(status__iexact="Rto")),
                daily_returned=Sum(Abs(F("collected_amount")), filter=Q(status__iexact="Returned")),
                daily_returned_count=Count("id", filter=Q(status__iexact="Returned")),
                daily_exchanged=Sum(Abs(F("collected_amount")), filter=Q(status__iexact="Exchanged")),
                daily_exchanged_count=Count("id", filter=Q(status__iexact="Exchanged")),
            )
            .order_by("order_date__date", "skucode")
        )

        return Response({
            "current_period": {
                "start_date": start_date,
                "end_date": end_date,
                "summary": current_summary
            },
            "previous_period": {
                "start_date": prev_start_date,
                "end_date": prev_end_date,
                "summary": previous_summary
            },
            "comparison_percent": comparison_detail,
            "daily": list(daily_data)
        })
