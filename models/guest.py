from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HotelGuest(models.Model):
    _name = 'hotel.guest'
    _description = 'Hotel Guest Registry'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete='cascade')
    nationality_id = fields.Many2one('res.country', string='Nationality')
    id_type = fields.Selection([
        ('passport', 'Passport'),
        ('national_id', 'National ID')
    ], string='ID Type')
    id_number = fields.Char(string='ID/Passport Number', required=True)
    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    vip = fields.Boolean(string='VIP Guest', default=False)
    blacklisted = fields.Boolean(string='Blacklisted', default=False)
    total_stays = fields.Integer(string='Total Stays', compute='_compute_total_stays')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True)
<<<<<<< HEAD
    # Inherit balance field from hotel_reservation
    
    reservation_ids = fields.One2many('hotel.reservation', 'guest_id', string='Reservations')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    deposit = fields.Monetary(string='Deposit', currency_field='currency_id')
    charges = fields.Monetary(string='Charges', compute='_compute_balance', store=True, currency_field='currency_id')
    balance = fields.Monetary(string='Balance', compute='_compute_balance', store=True, currency_field='currency_id')
=======
    total_stays = fields.Integer(
        string='Total Stays', compute='_compute_total_stays'
    )
>>>>>>> e58f499f74761fc542cc78bd49a2d919ef5c3998

    
    @api.depends('deposit', 'reservation_ids.state','reservation_ids.room_total','reservation_ids.folio_line_ids.amount')
    def _compute_balance(self):
        for g in self:
            res = g.reservation_ids.filtered(lambda r: r.state not in ('cancelled', 'no_show'))
            g.charges = sum(res.mapped('room_total')) + sum(res.mapped('folio_line_ids.amount'))
            g.balance = (g.deposit or 0.0) - (g.charges or 0.0)
    
    _sql_constraints = [
        ('unique_id_number', 'unique(id_number)', 'The ID/Passport number must be unique!')
    ]
    balance = fields.Float(string='Balance', )
    reservation_ids = fields.One2many(
        'hotel.reservation',
        'guest_id',
        string='Reservations'
    )


    def action_view_reservations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reservations'),
                'message': _('No reservations found for this guest.'),
                'type': 'info',
                'sticky': False,
            }
        }

    @api.constrains('vip', 'blacklisted')
    def _check_vip_blacklisted(self):
        for record in self:
            if record.vip and record.blacklisted:
                raise ValidationError(_("A guest cannot be both VIP and Blacklisted at the same time!"))

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        for record in self:
            if record.date_of_birth and record.date_of_birth >= fields.Date.today():
                raise ValidationError(_("Date of birth cannot be today or in the future!"))

    @api.constrains('id_number')
    def _check_id_number_format(self):
        for record in self:
            if record.id_number and len(record.id_number.strip()) < 5:
                raise ValidationError(_("Invalid ID/Passport number! Please check and enter a correct number."))

    @api.onchange('blacklisted')
    def _onchange_blacklisted(self):
        if self.blacklisted:
            self.active = False
        else:
            self.active = True

    @api.depends('partner_id')
    def _compute_total_stays(self):
        for record in self:
            if 'hotel.reservation' in self.env:
                try:
                    # بيحسب عدد الحجوزات من موديل الحجوزات عادي جداً
                    record.total_stays = self.env['hotel.reservation'].search_count([
                        ('guest_id', '=', record.id)
                    ])
                except Exception:
                    record.total_stays = 0
            else:
                record.total_stays = 0

    def action_view_reservations(self):
        """Action للـ Stat Button بيفتح قائمة حجوزات النزيل ده فقط"""
        self.ensure_one()
        return {
            'name': _('Guest Reservations'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation',
            'view_mode': 'tree,form',
            'domain': [('guest_id', '=', self.id)],
            'context': {'default_guest_id': self.id},
        }