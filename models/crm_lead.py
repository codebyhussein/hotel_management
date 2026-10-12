from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # -------------------------------------------------
    # Hotel inquiry fields
    # -------------------------------------------------
    lead_source = fields.Selection(
        [
            ('website', 'Website'),
            ('api', 'API'),
            ('manual', 'Manual'),
        ],
        string='Inquiry Source',
        default='manual',
        tracking=True,
    )
    room_id = fields.Many2one(
        'hotel.room',
        string='Room Name',
        tracking=True,
    )
    id_number = fields.Char(string='ID/Passport Number')
    balance = fields.Float(string='Balance', default=0.0)
    check_in = fields.Date(string='Check-in')
    check_out = fields.Date(string='Check-out')

    # Normal stored fields: the data typed on the lead is kept here
    # and copied to the reservation when converting.
    adults = fields.Integer(string='Adults', default=1)
    children = fields.Integer(string='Children', default=0)

    guest_id = fields.Many2one(
        'hotel.guest',
        string='Guest',
        copy=False,
        tracking=True,
    )
    reservation_id = fields.Many2one(
        'hotel.reservation',
        string='Reservation',
        copy=False,
        tracking=True,
    )

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    @api.constrains('check_in', 'check_out')
    def _check_hotel_dates(self):
        for lead in self:
            if lead.check_in and lead.check_out and lead.check_out <= lead.check_in:
                raise UserError(_('Check-out must be after check-in.'))

    # -------------------------------------------------
    # Convert: lead -> hotel.guest + draft reservation
    # -------------------------------------------------
    def _clean_context(self):
        """The CRM form puts default_type='opportunity' (and other default_*
        keys) in the context. They leak into res.partner / hotel.guest
        creation and break it, so remove them before creating records."""
        return {
            key: value
            for key, value in self.env.context.items()
            if not key.startswith('default_')
        }

    def _get_or_create_guest(self):
        """Reuse an existing guest (matched by email) or create a new one."""
        self.ensure_one()
        Guest = self.env['hotel.guest'].with_context(self._clean_context())

        if self.email_from:
            guest = Guest.search([('email', '=ilike', self.email_from)], limit=1)
            if guest:
                return guest

        guest_name = self.contact_name or self.partner_name or self.name
        if not guest_name:
            raise UserError(_('Please enter a contact name before converting.'))

        if not self.id_number:
            raise UserError(
                _('Please enter the guest ID/Passport Number before converting.')
            )

        return Guest.create({
            'name': guest_name,
            'email': self.email_from,
            'phone': self.phone,
            'id_number': self.id_number,
            'balance': self.balance,
        })

    def _prepare_reservation_vals(self, guest):
        """Adjust the keys below to match your hotel.reservation fields."""
        self.ensure_one()
        vals = {
            # core data taken from the lead
            'guest_id': guest.id,
            'room_id': self.room_id.id,
            'check_in': self.check_in,
            'check_out': self.check_out,
            'adults': self.adults,
            'children': self.children,
            'balance': self.balance,
            # always draft
            'state': 'draft',
            # optional contact / notes fields (used only if they exist)
            'guest_name': guest.display_name,
            'email': self.email_from,
            'phone': self.phone,
            'notes': self.description,
        }
        # Keep only the keys that really exist on hotel.reservation,
        # so a missing optional field never breaks the conversion.
        reservation_fields = self.env['hotel.reservation']._fields
        return {key: value for key, value in vals.items() if key in reservation_fields}

    def action_convert_to_guest_reservation(self):
        self.ensure_one()

        if self.reservation_id:
            raise UserError(_('This lead is already converted to a reservation.'))
        if not (self.check_in and self.check_out):
            raise UserError(_('Please set check-in and check-out dates first.'))

        guest = self._get_or_create_guest()
        reservation = self.env['hotel.reservation'].with_context(
            self._clean_context()
        ).create(
            self._prepare_reservation_vals(guest)
        )

        self.write({
            'guest_id': guest.id,
            'reservation_id': reservation.id,
        })
        self.message_post(
            body=_('Converted to guest %(guest)s and draft reservation %(res)s.',
                   guest=guest.display_name, res=reservation.display_name),
            subtype_xmlid='mail.mt_note',
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reservation'),
            'res_model': 'hotel.reservation',
            'res_id': reservation.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_reservation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reservation'),
            'res_model': 'hotel.reservation',
            'res_id': self.reservation_id.id,
            'view_mode': 'form',
            'target': 'current',
        }