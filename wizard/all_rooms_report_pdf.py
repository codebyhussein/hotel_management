# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class RoomHistoryReportWizard(models.TransientModel):
    _name = 'hotel.room.history.wizard'
    _description = 'Room History Report Wizard'

    date_from = fields.Date(
        string='Date From',
        required=True,
        default=fields.Date.today,
    )

    date_to = fields.Date(
        string='Date To',
        required=True,
        default=fields.Date.today,
    )

    def action_print_report(self):
        self.ensure_one()

        if self.date_from > self.date_to:
            raise ValidationError(
                _('Date From must be before or equal to Date To.')
            )

        return self.env.ref(
            'hotel_management.action_report_room_history_pdf'
        ).report_action(self)