from odoo import models, fields, api
from odoo.exceptions import UserError


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    folio_line_ids = fields.One2many('hotel.folio.line', 'reservation_id', string='Folio')
    payment_ids = fields.One2many('hotel.payment', 'reservation_id', string='Payments')

    folio_total = fields.Monetary(compute='_compute_balance', store=True)
    paid_amount = fields.Monetary(compute='_compute_balance', store=True)
    balance = fields.Monetary(compute='_compute_balance', store=True)

    @api.depends('room_total', 'folio_line_ids.amount','payment_ids.amount', 'payment_ids.state')
    def _compute_balance(self):
        for r in self:
            r.folio_total = sum(r.folio_line_ids.mapped('amount'))
            posted = r.payment_ids.filtered(lambda p: p.state == 'posted')
            r.paid_amount = sum(posted.mapped('amount'))
            r.balance = r.room_total + r.folio_total - r.paid_amount

    def action_check_out(self):
        for r in self:
            if r.state != 'checked_in':
                raise UserError("Only checked-in reservations can be checked out.")
        for r in self:
            if r.currency_id.compare_amounts(r.balance, 0) > 0:
                raise UserError(
                    "Outstanding balance: %s. Register the payment before check-out."
                    % r.balance)
            r.folio_line_ids.write({'is_paid': True})
        return super().action_check_out()