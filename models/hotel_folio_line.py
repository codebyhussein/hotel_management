# from odoo import models, fields, api


# class HotelFolioLine(models.Model):
#     _name = "hotel.folio.line"
#     _description = "Folio Line"

#     reservation_id = fields.Many2one(
#         "hotel.reservation", required=True, ondelete="cascade"
#     )
#     product_id = fields.Many2one("product.product")
#     name = fields.Char(required=True)
#     charge_type = fields.Selection(
#         [
#             ("food", "Food"),
#             ("minibar", "Minibar"),
#             ("laundry", "Laundry"),
#             ("service", "Service"),
#             ("other", "Other"),
#         ],
#         default="service",
#     )
#     charge_date = fields.Date(default=fields.Date.context_today)
#     quantity = fields.Float(default=1)
#     unit_price = fields.Monetary()
#     currency_id = fields.Many2one(related="reservation_id.currency_id", store=True)
#     amount = fields.Monetary(compute="_compute_amount", store=True)
#     is_paid = fields.Boolean()
#     invoice_id = fields.Many2one("account.move", readonly=True)

#     @api.depends("quantity", "unit_price")
#     def _compute_amount(self):
#         for product in self:
#             product.amount = product.quantity * product.unit_price

#     # Update product name and unit_price
#     @api.onchange("product_id")
#     def _onchange_product(self):
#         if self.product_id:
#             self.name = self.product_id.name
#             self.unit_price = self.product_id.list_price
