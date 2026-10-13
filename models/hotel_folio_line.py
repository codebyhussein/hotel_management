from odoo import models, fields, api


class HotelFolioLine(models.Model):
    _name = "hotel.folio.line"
    _description = "Folio Line"

    reservation_id = fields.Many2one(
        "hotel.reservation", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.product")
    name = fields.Char(required=True)
    charge_type = fields.Selection(
        [
            ("food", "Food"),
            ("minibar", "Minibar"),
            ("laundry", "Laundry"),
            ("service", "Service"),
            ("other", "Other"),
        ],
        default="service",
    )
    charge_date = fields.Date(default=fields.Date.context_today)
    quantity = fields.Float(default=1)
    unit_price = fields.Monetary()
    currency_id = fields.Many2one(
        related="reservation_id.currency_id", store=True)
    amount = fields.Monetary(compute="_compute_amount", store=True)
    is_paid = fields.Boolean()
    task_id = fields.Many2one('hotel.housekeeping.task', string='Room Service Task')
    # invoice_id = fields.Many2one("account.move", readonly=True)

    @api.depends("quantity", "unit_price")
    def _compute_amount(self):
        for rec in self:
            rec.amount = (rec.quantity or 0.0) * (rec.unit_price or 0.0)

    @api.onchange('task_id')
    def _onchange_task_id(self):
        if self.task_id and not self.reservation_id:
            self.reservation_id = self.task_id.reservation_id

    @api.onchange("product_id")
    def _onchange_product(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name
                rec.unit_price = rec.product_id.list_price
