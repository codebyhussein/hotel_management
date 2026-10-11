# -*- coding: utf-8 -*-

from odoo import models, fields, _


class RoomTaskWizard(models.TransientModel):
    _name = 'room.task.wizard'
    _description = 'Room Maintenance / Housekeeping Wizard'

    # =========================================
    # Room Information
    # =========================================

    room_id = fields.Many2one(
        'hotel.room',
        string='Room',
        required=True,
        readonly=True,
    )

    # =========================================
    # Task Information
    # =========================================

    task_type = fields.Selection(
        [
            ('maintenance', 'Maintenance'),
            ('housekeeping', 'Housekeeping'),
        ],
        string='Task Type',
        required=True,
        default='maintenance',
    )

    name = fields.Char(
        string='Task Title',
        required=True,
    )

    maintenance_type = fields.Selection(
        [
            ('plumbing', 'Plumbing'),
            ('electrical', 'Electrical'),
            ('ac', 'AC / HVAC'),
            ('furniture', 'Furniture / Carpentry'),
            ('other', 'Other'),
        ],
        string='Maintenance Type',
    )

    priority = fields.Selection(
        [
            ('0', '0 - Very Low'),
            ('1', '1 - Low'),
            ('2', '2 - Normal'),
            ('3', '3 - Medium'),
            ('4', '4 - High'),
            ('5', '5 - Urgent'),
        ],
        string='Priority',
        required=True,
        default='0',
    )

    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned Staff',
    )

    description = fields.Text(
        string='Description',
    )

    # =========================================
    # Create Maintenance / Housekeeping Task
    # =========================================

    def action_create_task(self):
        self.ensure_one()

        # Maintenance Type is required for maintenance tasks.
        if self.task_type == 'maintenance' and not self.maintenance_type:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Missing Information'),
                    'message': _(
                        'Please select a Maintenance Type.'
                    ),
                    'type': 'warning',
                    'sticky': False,
                },
            }

        # Prepare task values.
        task_values = {
            'name': self.name,
            'room_id': self.room_id.id,
            'task_type': self.task_type,
            'priority': self.priority,
            'assigned_user_id': self.assigned_user_id.id or False,
            'description': self.description or False,
        }

        # Maintenance Type applies only to maintenance tasks.
        if self.task_type == 'maintenance':
            task_values['maintenance_type'] = self.maintenance_type
        else:
            task_values['maintenance_type'] = False

        # Create the actual task.
        task = self.env['hotel.housekeeping.task'].create(
            task_values
        )

        # Open the created task.
        return {
            'type': 'ir.actions.act_window',
            'name': _('Created Task'),
            'res_model': 'hotel.housekeeping.task',
            'res_id': task.id,
            'view_mode': 'form',
            'target': 'current',
        }