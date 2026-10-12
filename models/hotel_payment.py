from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HotelPayment(models.Model):
    _name = 'hotel.payment'
    _description = 'Hotel Payment'
    _order = 'payment_date desc, id desc'

    reservation_id = fields.Many2one(
        'hotel.reservation', required=True, ondelete='cascade')
    folio_line_id = fields.Many2one(
        'hotel.folio.line', domain="[('reservation_id', '=', reservation_id)]")
    partner_id = fields.Many2one(
        'res.partner', related='reservation_id.guest_id.partner_id', store=True)
    currency_id = fields.Many2one(
        'res.currency', related='reservation_id.currency_id', store=True)
    payment_date = fields.Date(default=fields.Date.context_today, required=True)
    amount = fields.Monetary(required=True)
    method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Credit Card'),
        ('transfer', 'Bank Transfer'),
    ], default='cash', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True)
    reference = fields.Char()

    @api.constrains('amount')
    def _check_amount(self):
        for p in self:
            if p.amount <= 0:
                raise ValidationError("Payment amount must be greater than zero.")

    def action_confirm(self):
        self.write({'state': 'posted'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})