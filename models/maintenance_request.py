# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import timedelta


class HotelMaintenanceRequest(models.Model):
    _name = 'hotel.maintenance.request'
    _description = 'Hotel Room Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'urgency desc, create_date desc'

    name = fields.Char(
        string='Maintenance Ref',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('hotel.maintenance.sequence') or _('New')
    )

    # Links to Hotel Models
    room_id = fields.Many2one(
        'hotel.room',
        string='Room',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    property_id = fields.Many2one(
        related='room_id.property_id',
        string='Property',
        store=True,
        readonly=True
    )
    reservation_id = fields.Many2one(
        'hotel.reservation',
        string='Current Reservation',
        domain="[('room_id', '=', room_id), ('state', '=', 'checked_in')]"
    )
    guest_id = fields.Many2one(
        related='reservation_id.guest_id',
        string='Guest Name',
        store=True,
        readonly=True
    )

    issue_type = fields.Selection([
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('air_condition', 'AC / HVAC'),
        ('furniture', 'Carpentry / Furniture'),
        ('appliance', 'Electronics / TV'),
        ('other', 'Other')
    ], string='Issue Type', required=True, default='plumbing', tracking=True)

    # 5 Stars Urgency Selection (0 to 4)
    urgency = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
        ('4', 'Emergency')
    ], string='Urgency', default='2', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    description = fields.Text(string='Description', required=True)
    assigned_to = fields.Many2one('res.users', string='Assigned Staff', tracking=True)

    preferred_date = fields.Date(string='Preferred Repair Date')
    scheduled_date = fields.Date(string='Scheduled Date')
    completion_date = fields.Date(string='Completion Date', readonly=True)
    actual_cost = fields.Float(string='Actual Cost', default=0.0)

    # 1. تحديث لحظي في الواجهة عند تغيير الـ Urgency
    @api.onchange('urgency')
    def _onchange_urgency_date(self):
        for rec in self:
            if rec.urgency == '4':
                rec.scheduled_date = fields.Date.today() + timedelta(days=1)
            else:
                rec.scheduled_date = False

    # 2. ضمان تعيين تاريخ الطوارئ وحفظه فعلياً في قاعدة البيانات عند الإنشاء (Create)
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('urgency') == '4' and not vals.get('scheduled_date'):
                vals['scheduled_date'] = fields.Date.today() + timedelta(days=1)
        return super(HotelMaintenanceRequest, self).create(vals_list)

    # 3. ضمان الحفظ والتحديث عند التعديل (Write)
    def write(self, vals):
        if vals.get('urgency') == '4' and not self.scheduled_date:
            vals['scheduled_date'] = fields.Date.today() + timedelta(days=1)
        return super(HotelMaintenanceRequest, self).write(vals)

    # Workflow Actions
    def action_start_maintenance(self):
        for rec in self:
            rec.state = 'in_progress'
            if rec.room_id:
                rec.room_id.write({'status': 'maintenance'})

    def action_set_done(self):
        for rec in self:
            rec.write({
                'state': 'done',
                'completion_date': fields.Date.today()
            })
            if rec.room_id:
                rec.room_id.write({'status': 'available'})

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    # Cron Job 1: Auto Schedule Emergency Repairs
    @api.model
    def _cron_set_emergency_date(self):
        emergency_requests = self.search([
            ('urgency', '=', '4'),
            ('scheduled_date', '=', False),
            ('state', 'in', ['draft', 'in_progress'])
        ])
        tomorrow = fields.Date.today() + timedelta(days=1)
        for req in emergency_requests:
            req.scheduled_date = tomorrow

    # Email Notification Helper
    def send_maintenance_email(self):
        template = self.env.ref('hotel_management.email_template_hotel_maintenance', raise_if_not_found=False)
        if not template:
            return

        for req in self:
            if req.assigned_to and req.assigned_to.email:
                template.send_mail(req.id, force_send=True)

    # Cron Job 2: Send Reminder for Preferred Repair Date
    @api.model
    def _cron_maintenance_reminder(self):
        tomorrow = fields.Date.today() + timedelta(days=1)
        requests = self.search([
            ('preferred_date', '=', tomorrow),
            ('state', 'not in', ['done', 'cancelled'])
        ])
        requests.send_maintenance_email()