from odoo import models, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, time, timedelta


class RoomStatusReportWizard(models.TransientModel):
    _name = 'room.status.report.wizard'
    _description = 'Room Status Report Wizard'

    date_from = fields.Date(
        string='Date From',
        required=True,
    )

    date_to = fields.Date(
        string='Date To',
        required=True,
    )

    property_id = fields.Many2one(
        'hotel.property',
        string='Property',
    )

    status = fields.Selection(
        [
            ('available', 'Available'),
            ('occupied', 'Occupied'),
            ('maintenance', 'Under Maintenance'),
            ('needs_cleaning', 'Needs Cleaning'),
        ],
        string='Room Status',
    )

    def action_apply(self):
        self.ensure_one()

        if self.date_from > self.date_to:
            raise ValidationError(
                _('Date From must be before or equal to Date To.')
            )

        # Convert the selected dates to a datetime range.
        date_from = datetime.combine(
            self.date_from,
            time.min,
        )

        date_to = datetime.combine(
            self.date_to + timedelta(days=1),
            time.min,
        )

        # Build the report domain.
        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<', date_to),
        ]

        if self.property_id:
            domain.append(
                ('property_id', '=', self.property_id.id)
            )

        if self.status:
            domain.append(
                ('status', '=', self.status)
            )

        # Open the existing room status graph.
        action = self.env.ref(
            'hotel_management.action_hotel_room_report'
        ).read()[0]

        action['domain'] = domain
        action['context'] = {
            'graph_mode': 'pie',
        }

        return action