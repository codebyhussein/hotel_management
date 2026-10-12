from odoo import models, fields , api
from odoo.exceptions import ValidationError

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _order = 'room_number asc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # =========================
    # Room Information
    # =========================

    room_number = fields.Char(
        string='Room Number',
        required=True,
        index=True
    )

    room_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('suite', 'Suite'),
    ], string='Room Type', required=True)

    price = fields.Float(
        string='Price',
        required=True
    )

    capacity = fields.Integer(
        string='Capacity',
        compute='_compute_capacity',
        store=True,
        readonly=True,
    )
    nightly_rate = fields.Float(
        related='price',
        string='Nightly Rate',
    )

    property_id = fields.Many2one(
        'hotel.property',
        string='Property',
        required=True,
        ondelete='restrict',
        index=True,
        default=lambda self: self.env.user.property_id,
    )
    employee_name = fields.Many2one(
    'res.users',
    string='Employee Name',
    required=True,
    
    index=True,
   
    )

    description = fields.Text(
    string='Description'
    )
    floor_number = fields.Integer(
    string='Floor Number'
    )

        # All reservations linked to this room
    reservation_ids = fields.One2many(
        'hotel.reservation',
        'room_id',
        string='Reservations'
    )

    reservation_count = fields.Integer(
        string='Reservations Count',
        compute='_compute_room_history_counts'
    )

    # All housekeeping and maintenance tasks linked to this room
    housekeeping_task_ids = fields.One2many(
        'hotel.housekeeping.task',
        'room_id',
        string='Housekeeping Tasks'
    )

    maintenance_count = fields.Integer(
        string='Maintenance Count',
        compute='_compute_room_history_counts'
    )



    
    # =========================
    # Room Status
    # =========================



    status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('needs_cleaning', 'Needs Cleaning'),
    ], string='Status', default='available', required=True, tracking=True)
    @api.depends('room_number')
    def _compute_display_name(self):
        for room in self:
            room.display_name = f"Room {room.room_number}" if room.room_number else 'New Room'
    @api.depends('room_type')
    def _compute_capacity(self):
        capacity_map = {
            'single': 1,
            'double': 2,
            'triple': 3,
            'suite': 2,
        }
        for room in self:
            room.capacity = capacity_map.get(room.room_type, 0)
    def action_set_available(self):
        self.write({'status': 'available'})

    def action_set_occupied(self):
        self.write({'status': 'occupied'})

    def action_set_maintenance(self):
        self.write({'status': 'maintenance'})

    def action_set_needs_cleaning(self):
        self.write({'status': 'needs_cleaning'})

    @api.depends(
    'reservation_ids',
    'housekeeping_task_ids',
    'housekeeping_task_ids.task_type'
    )
    def _compute_room_history_counts(self):
        for room in self:
            room.reservation_count = len(room.reservation_ids)

            room.maintenance_count = len(
                room.housekeeping_task_ids.filtered(
                    lambda task: task.task_type == 'maintenance'
                )
            )
    def action_view_reservations(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Room Reservations',
            'res_model': 'hotel.reservation',
            'view_mode': 'tree,form',
            'domain': [
                ('room_id', '=', self.id)
            ],
            'context': {
                'default_room_id': self.id,
            },
        }


    def action_view_maintenance(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Room Maintenance',
            'res_model': 'hotel.housekeeping.task',
            'view_mode': 'tree,form',
            'domain': [
                ('room_id', '=', self.id),
                ('task_type', '=', 'maintenance'),
            ],
            'context': {
                'default_room_id': self.id,
                'default_task_type': 'maintenance',
            },
        }
    def action_open_room_history_report(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Room History Report',
            'res_model': 'room.history.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_room_id': self.id,
            },
        }

    def action_open_room_task_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Maintenance / Housekeeping',
            'res_model': 'room.task.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'hotel_management.view_room_task_wizard_form'
            ).id,
            'target': 'new',
            'context': {
                'default_room_id': self.id,
            },
        }
    @api.constrains('room_number', 'property_id')
    def _check_room_number_unique(self):
        for room in self:
            if room.room_number and room.property_id:
                existing_room = self.search([
                    ('room_number', '=', room.room_number),
                    ('property_id', '=', room.property_id.id),
                    ('id', '!=', room.id),
                ], limit=1)

                if existing_room:
                    raise ValidationError(
                        'Room number must be unique within the same property!'
                    )