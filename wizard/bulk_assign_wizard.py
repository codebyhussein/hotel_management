from odoo import models, fields, api


class BulkAssignWizard(models.TransientModel):
    _name = 'hotel.bulk.assign.wizard'
    _description = 'Bulk Assign Staff Wizard'

    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned Staff',
        required=True
    )

    def action_confirm_assign(self):

        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])

        if active_model and active_ids:
            records = self.env[active_model].browse(active_ids)

            if hasattr(records, 'assigned_user_id'):
                records.write({'assigned_user_id': self.assigned_user_id.id})

        return {'type': 'ir.actions.act_window_close'}