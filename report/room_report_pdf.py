from odoo import models, fields
from datetime import datetime, time


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

            # ==========================================
            # Reservation History
            # ==========================================
            reservations = Reservation.browse()

            if wizard.include_reservations:
                reservation_domain = [
                    ('room_id', '=', room.id),
                    ('state', '=', 'checked_out'),
                ]

                if wizard.date_from:
                    reservation_domain.append(
                        ('check_out', '>=', wizard.date_from)
                    )

                if wizard.date_to:
                    reservation_domain.append(
                        ('check_out', '<=', wizard.date_to)
                    )

                reservations = Reservation.search(
                    reservation_domain,
                    order='check_out asc',
                )

            # ==========================================
            # Maintenance, Housekeeping & Room Service
            # ==========================================
            tasks = Task.browse()

            if wizard.include_tasks:
                task_domain = [
                    ('room_id', '=', room.id),
                ]

                # Filter by request date
                if wizard.date_from:
                    date_from_datetime = datetime.combine(
                        wizard.date_from,
                        time.min,
                    )

                    task_domain.append(
                        (
                            'request_date',
                            '>=',
                            fields.Datetime.to_string(
                                date_from_datetime
                            ),
                        )
                    )

                if wizard.date_to:
                    date_to_datetime = datetime.combine(
                        wizard.date_to,
                        time.max,
                    )

                    task_domain.append(
                        (
                            'request_date',
                            '<=',
                            fields.Datetime.to_string(
                                date_to_datetime
                            ),
                        )
                    )

                # Filter by task type
                if wizard.task_type != 'all':
                    task_domain.append(
                        ('task_type', '=', wizard.task_type)
                    )

                tasks = Task.search(
                    task_domain,
                    order='request_date asc',
                )

            # ==========================================
            # Report Data
            # ==========================================
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