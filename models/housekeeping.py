from odoo import models, fields, api

class HotelHousekeepingTask(models.Model):
    _name = 'hotel.housekeeping.task'
    _description = 'Housekeeping Task'

    room_id = fields.Many2one('hotel.room', string='Room')
    name = fields.Char(string='Task Title', required=True)
    assigned_user_id = fields.Many2one('res.users', string='Assigned Staff')

    task_type = fields.Selection([
        ('housekeeping', 'Housekeeping'),
        ('maintenance', 'Maintenance')
    ], default='housekeeping', string='Task Type')

    maintenance_type = fields.Selection([
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('ac', 'AC / HVAC'),
        ('furniture', 'Furniture / Carpentry'),
        ('other', 'Other')
    ], string='Maintenance Type')

    priority = fields.Selection([
        ('0', '0 - Very Low'),
        ('1', '1 - Low'),
        ('2', '2 - Normal'),
        ('3', '3 - Medium'),
        ('4', '4 - High'),
        ('5', '5 - Urgent')
    ], default='0', string='Priority')

    state = fields.Selection([
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], default='todo')

    scheduled_date = fields.Date(
        string='Scheduled Date',
        compute='_compute_scheduled_date',
        store=True,
        readonly=False
    )

    start_date = fields.Datetime(string='Start Date')
    done_date = fields.Datetime(string='Done Date')
    description = fields.Text(string='Description')

    @api.depends('priority')
    def _compute_scheduled_date(self):
        for rec in self:
            if rec.priority and str(rec.priority) == '5':
                rec.scheduled_date = fields.Date.context_today(self)
            else:
                rec.scheduled_date = False

    def action_mark_in_progress(self):
        for rec in self:
            rec.state = 'in_progress'
            rec.start_date = fields.Datetime.now()

    def action_mark_done(self):
        for rec in self:
            rec.state = 'done'
            rec.done_date = fields.Datetime.now()
            if rec.room_id:
                rec.room_id.write({'status': 'available'})