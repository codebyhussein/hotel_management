from odoo import models, fields, api

class HotelHousekeepingTask(models.Model):
    _name = 'hotel.housekeeping.task'
    _description = 'Housekeeping Task'

    name = fields.Char(string='Task Title', required=True)
    assigned_user_id = fields.Many2one('res.users', string='Assigned Staff')

    task_type = fields.Selection([
        ('housekeeping', 'Housekeeping'),
        ('maintenance', 'Maintenance')
    ], default='housekeeping')

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High')
    ], default='0')

    state = fields.Selection([
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], default='todo')

    # تعديل الحقل ليصبح computed ومعموله store
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
            # المقارنة تضمن تحويل القيمة لـ string في حال أرسلها الـ widget كـ int
            if rec.priority and str(rec.priority) == '2':
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