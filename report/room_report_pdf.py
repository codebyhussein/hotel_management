from odoo import models


class RoomHistoryPDFReport(models.AbstractModel):
    _name = 'report.hotel_management.report_room_history_pdf'
    _description = 'Room History PDF Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['room.history.report.wizard'].browse(docids)

        report_data = {}

        Reservation = self.env['hotel.reservation']
        Task = self.env['hotel.housekeeping.task']

        for wizard in docs:
            room = wizard.room_id

            # Reservation History
            reservations = Reservation.browse()

            if wizard.include_reservations:
                reservation_domain = [
                    ('room_id', '=', room.id),
                    ('state', '=', 'checked_out'),
                    ('check_out', '>=', wizard.date_from),
                    ('check_out', '<=', wizard.date_to),
                ]

                reservations = Reservation.search(
                    reservation_domain,
                    order='check_out asc',
                )

            # Maintenance & Housekeeping History
            tasks = Task.browse()

            if wizard.include_tasks:
                task_domain = [
                    ('room_id', '=', room.id),
                    ('scheduled_date', '>=', wizard.date_from),
                    ('scheduled_date', '<=', wizard.date_to),
                ]

                if wizard.task_type != 'all':
                    task_domain.append(
                        ('task_type', '=', wizard.task_type)
                    )

                if wizard.maintenance_type != 'all':
                    task_domain.append(
                        ('maintenance_type', '=', wizard.maintenance_type)
                    )

                tasks = Task.search(
                    task_domain,
                    order='scheduled_date asc',
                )

            report_data[wizard.id] = {
                'room': room,
                'reservations': reservations,
                'tasks': tasks,
            }

        return {
            'doc_ids': docs.ids,
            'doc_model': 'room.history.report.wizard',
            'docs': docs,
            'report_data': report_data,
        }