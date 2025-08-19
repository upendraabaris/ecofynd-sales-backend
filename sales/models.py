from django.db import models
import uuid
from decimal import Decimal 
class SalesData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.IntegerField()
    status = models.TextField()
    vendor_name = models.TextField()
    order_date = models.DateTimeField()
    cod_prepaid = models.IntegerField()
    customer_name = models.TextField()
    customer_state = models.TextField()
    category = models.TextField()
    skucode = models.TextField()
    listing_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    cod_charges = models.DecimalField(max_digits=10, decimal_places=2)
    units_sold = models.IntegerField()
    gst_on_sales = models.DecimalField(max_digits=10, decimal_places=2)
    collected_amount = models.DecimalField(max_digits=10, decimal_places=2)
    penalty = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price_wo_tax = models.DecimalField(max_digits=10, decimal_places=2)
    vendor_transfer = models.DecimalField(max_digits=10, decimal_places=2)
    net_gst = models.DecimalField(max_digits=10, decimal_places=2)
    tds = models.DecimalField(max_digits=10, decimal_places=2)
    tcs = models.DecimalField(max_digits=10, decimal_places=2)
    vaaree_payment = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_no = models.TextField()
    fulfilled_by = models.TextField()
    seller_state = models.TextField()
    invoice_date = models.DateField()
    actual_product_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'sales_data'  # important since you're using existing table

    # def profit(self):
    #     if self.status.strip().upper() == 'Rto':
    #         return None  # Or return "Excluded (RTO)"

    #     # 1. Final Cost per unit
    #     overhead = self.selling_price * Decimal('0.10')
    #     final_cost_per_unit = self.cost_price_wo_tax + overhead

    #     # 2. Total Final Cost
    #     total_final_cost = final_cost_per_unit * self.units_sold

    #     # 3. Profit Amount
    #     profit_amount = self.vendor_transfer - total_final_cost

    #     # 4. Profit Percentage (avoid division by zero)
    #     if self.vendor_transfer > 0:
    #         profit_percent = (profit_amount / self.vendor_transfer) * 100
    #     else:
    #         profit_percent = Decimal('0.00')

    #     return {
    #         "profit_amount": round(profit_amount, 2),
    #         "profit_percent": round(profit_percent, 2),
    #         "status": "Profit" if profit_amount > 0 else "Loss"
    #     }
    # def profit(self):
    #     if self.status.strip().lower() in ['rto', 'returned']:
    #         return None  # Exclude RTO and Returned orders

    #     try:
    #         vendor_transfer = self.vendor_transfer 
    #         overhead = self.selling_price * Decimal('0.10')
    #         total_cost = self.actual_product_price * self.units_sold
    #         profit_amount = self.vendor_transfer - (total_cost + overhead)

    #         # To avoid division by zero
    #         if self.selling_price > 0:
    #             profit_percent = (profit_amount / self.selling_price) * 100
    #         else:
    #             profit_percent = Decimal('0.00')

    #         return {
    #             "profit_amount": round(profit_amount, 2),
    #             "profit_percent": round(profit_percent, 2),
    #             "status": "Profit" if profit_amount > 0 else "Loss"
    #         }
    #     except Exception as e:
    #         return {"error": str(e)}


