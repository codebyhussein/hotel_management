# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RoomHistoryPdfReport(models.AbstractModel):
    _name = 'report.hotel_management.report_room_history_pdf'
    _description = 'Hotel Room History PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # ==========================================
        # 1. بيانات الـ Wizard والفترة المختارة
        # ==========================================
        wizard = self.env['hotel.room.history.wizard'].browse(
            docids
        ).exists()

        if not wizard:
            wizard = self.env['hotel.room.history.wizard'].browse(
                data.get('wizard_id')
            ).exists() if data and data.get('wizard_id') else wizard

        wizard.ensure_one()

        date_from = fields.Date.to_date(wizard.date_from)
        date_to = fields.Date.to_date(wizard.date_to)

        # ==========================================
        # 2. جلب جميع الغرف
        # ==========================================
        rooms = self.env['hotel.room'].search(
            [],
            order='property_id, room_number'
        )

        # ==========================================
        # 3. جلب الحجوزات المتداخلة مع الفترة
        # ==========================================
        reservations = self.env['hotel.reservation'].search([
            ('check_in', '<=', date_to),
            ('check_out', '>=', date_from),
        ], order='check_in asc')

        # ==========================================
        # 4. جلب طلبات الصيانة
        # ==========================================
        all_maintenance = self.env[
            'hotel.maintenance.request'
        ].search([])

        maintenance_requests = self.env[
            'hotel.maintenance.request'
        ]

        for request in all_maintenance:
            # تحديد التاريخ المعتمد لطلب الصيانة
            request_date = (
                request.scheduled_date
                or request.preferred_date
            )

            if request_date:
                request_date = fields.Date.to_date(
                    request_date
                )

            elif request.create_date:
                request_date = fields.Datetime.to_datetime(
                    request.create_date
                ).date()

            # الاحتفاظ بالطلبات الواقعة داخل الفترة
            if (
                request_date
                and date_from <= request_date <= date_to
            ):
                maintenance_requests |= request

        # ==========================================
        # 5. تجميع الحجوزات والصيانة لكل غرفة
        # ==========================================
        histories = {}

        for room in rooms:
            room_reservations = reservations.filtered(
                lambda reservation:
                    reservation.room_id.id == room.id
            )

            room_maintenance = maintenance_requests.filtered(
                lambda request:
                    request.room_id.id == room.id
            )

            histories[room.id] = {
                'reservations': room_reservations,
                'maintenance': room_maintenance,
            }

        # ==========================================
        # 6. تجميع تكاليف الصيانة حسب نوع المشكلة
        # ==========================================
        issue_types = dict(
            self.env['hotel.maintenance.request']
            ._fields['issue_type'].selection
        )

        maintenance_summary = []

        for issue_type, issue_label in issue_types.items():
            requests = maintenance_requests.filtered(
                lambda request:
                    request.issue_type == issue_type
            )

            total_cost = sum(
                requests.mapped('actual_cost')
            )

            maintenance_summary.append({
                'type': issue_type,
                'label': issue_label,
                'count': len(requests),
                'total_cost': total_cost,
            })

        # ==========================================
        # 7. إجمالي تكاليف الصيانة
        # ==========================================
        total_maintenance_cost = sum(
            maintenance_requests.mapped('actual_cost')
        )

        # ==========================================
        # 8. البيانات التي سيستخدمها قالب PDF
        # ==========================================
        return {
            'doc_ids': wizard.ids,
            'doc_model': 'hotel.room.history.wizard',
            'docs': wizard,

            'rooms': rooms,
            'histories': histories,

            'date_from': date_from,
            'date_to': date_to,

            'maintenance_summary': maintenance_summary,
            'total_maintenance_cost': total_maintenance_cost,
        }