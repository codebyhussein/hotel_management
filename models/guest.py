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

    # حقل الـ Balance الإضافي
    balance = fields.Float(string='Balance', default=0.0)

    # تغيير الـ notes إلى description
    description = fields.Text(string='Description')

    active = fields.Boolean(string='Active', default=True)
    total_stays = fields.Integer(
        string='Total Stays', compute='_compute_total_stays'
    )

    _sql_constraints = [
        ('unique_id_number', 'unique(id_number)', 'The ID/Passport number must be unique!')
    ]
    balance = fields.Float(string='Balance', )
    reservation_ids = fields.One2many(
        'hotel.reservation',
        'guest_id',
        string='Reservations'
    )

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
                    record.total_stays = self.env['hotel.reservation'].search_count([
                        ('guest_id', '=', record.id)
                    ])
                except Exception:
                    record.total_stays = 0
            else:
                record.total_stays = 0

    def action_view_reservations(self):
        self.ensure_one()
        return {
            'name': _('Guest Reservations'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation',
            'view_mode': 'tree,form',
            'domain': [('guest_id', '=', self.id)],
            'context': {'default_guest_id': self.id},
        }