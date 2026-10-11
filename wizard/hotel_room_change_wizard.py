# -*- coding: utf-8 -*-
from odoo import models, fields


class HotelRoomChangeWizard(models.TransientModel):
    _name = 'hotel.reservation.room.change.wizard'
    _description = 'Change Room Wizard'

    reservation_id = fields.Many2one('hotel.reservation', required=True)
    current_room_id = fields.Many2one(related='reservation_id.room_id', string='Current Room')
    new_room_id = fields.Many2one('hotel.room', string='New Room', required=True)
    keep_rate = fields.Boolean(
        string='Keep current nightly rate',
        help='لو مش متعلّم، السعر هيتحدّث لسعر الغرفة الجديدة.')
    reason = fields.Text(string='Reason', required=True)

    def action_confirm_change(self):
        self.ensure_one()
        self.reservation_id._change_room(self.new_room_id, self.reason, self.keep_rate)
        return {'type': 'ir.actions.act_window_close'}