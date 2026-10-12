from odoo import models, fields, api
from odoo.exceptions import UserError


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    folio_line_ids = fields.One2many('hotel.folio.line', 'reservation_id', string='Folio')
    payment_ids = fields.One2many('hotel.payment', 'reservation_id', string='Payments')

    folio_total = fields.Monetary(compute='_compute_balance', store=True)
    paid_amount = fields.Monetary(compute='_compute_balance', store=True)
    balance = fields.Monetary(compute='_compute_balance', store=True)
    invoice_id = fields.Many2one('account.move', readonly=True, copy=False)
    
    @api.depends('room_total', 'folio_line_ids.amount','payment_ids.amount', 'payment_ids.state')
    def _compute_balance(self):
        for r in self:
            r.folio_total = sum(r.folio_line_ids.mapped('amount'))
            posted = r.payment_ids.filtered(lambda p: p.state == 'posted')
            r.paid_amount = sum(posted.mapped('amount'))
            r.balance = r.room_total + r.folio_total - r.paid_amount

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
        }

    def action_create_invoice(self):
        self.ensure_one()
        if self.invoice_id:
            raise UserError("An invoice already exists for this reservation.")

        lines = [(0, 0, {
            'name': f'Room {self.room_id.room_number} - {self.nights} nights',
            'quantity': self.nights,
            'price_unit': self.nightly_rate,
        })]
        for l in self.folio_line_ids:
            lines.append((0, 0, {
                'product_id': l.product_id.id,
                'name': l.name,
                'quantity': l.quantity,
                'price_unit': l.unit_price,
            }))

        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.guest_id.partner_id.id,
            'invoice_origin': self.name,
            'currency_id': self.currency_id.id,
            'invoice_line_ids': lines,
        })
        self.invoice_id = move
        self.folio_line_ids.write({'invoice_id': move.id})
        return move

    def action_check_out(self):
       for r in self:
           if r.state != 'checked_in':
               raise UserError("Only checked-in reservations can be checked out.")
       for r in self:
           if r.currency_id.compare_amounts(r.balance, 0) > 0:
               raise UserError(
                   "Outstanding balance: %s. Register the payment before check-out."
                   % r.balance)
           if not r.invoice_id:
               r.action_create_invoice()
           r.folio_line_ids.write({'is_paid': True})
       return super().action_check_out()