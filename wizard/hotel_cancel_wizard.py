# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HotelReservationCancelWizard(models.TransientModel):
    _name = 'hotel.reservation.cancel.wizard'
    _description = 'Cancel Reservation Wizard'

    reservation_id = fields.Many2one('hotel.reservation', required=True)
    currency_id = fields.Many2one(related='reservation_id.currency_id')
    reason = fields.Text(string='Cancellation Reason', required=True)
    cancellation_fee = fields.Monetary(
        compute='_compute_fee', currency_field='currency_id')
    deposit_refund = fields.Monetary(
        compute='_compute_fee', currency_field='currency_id')

    @api.depends('reservation_id')
    def _compute_fee(self):
        for wiz in self:
            res = wiz.reservation_id
            fee = res._get_cancellation_fee() if res else 0.0
            wiz.cancellation_fee = fee
            wiz.deposit_refund = res._refund_for_fee(fee) if res else 0.0

    def action_confirm_cancel(self):
        self.ensure_one()
        self.reservation_id._do_cancel(self.reason)
        return {'type': 'ir.actions.act_window_close'}