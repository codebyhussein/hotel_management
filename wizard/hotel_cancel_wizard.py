# -*- coding: utf-8 -*-
from odoo import models, fields


class HotelReservationCancelWizard(models.TransientModel):
    _name = 'hotel.reservation.cancel.wizard'
    _description = 'Cancel Reservation Wizard'

    reservation_id = fields.Many2one('hotel.reservation', required=True)
    reason = fields.Text(string='Cancellation Reason', required=True)

    def action_confirm_cancel(self):
        self.ensure_one()
        self.reservation_id._do_cancel(self.reason)
        return {'type': 'ir.actions.act_window_close'}