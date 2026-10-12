# -*- coding: utf-8 -*-

import io
import base64
import xlsxwriter

from datetime import datetime, date, time

from odoo import models, fields, _
from odoo.exceptions import UserError


class RoomHistoryReportWizard(models.TransientModel):
    _name = 'room.history.report.wizard'
    _description = 'Room History Excel Report'

    # =====================================================
    # Room
    # =====================================================

    room_id = fields.Many2one(
        'hotel.room',
        string='Room',
        required=True,
        readonly=True,
    )

    # =====================================================
    # Report Filters
    # =====================================================

    date_from = fields.Date(
        string='Date From',
    )

    date_to = fields.Date(
        string='Date To',
    )

    task_type = fields.Selection(
        [
            ('all', 'All Tasks'),
            ('maintenance', 'Maintenance'),
            ('housekeeping', 'Housekeeping'),
        ],
        string='Task Type',
        default='all',
    )

    maintenance_type = fields.Selection(
        [
            ('all', 'All Maintenance Types'),
            ('plumbing', 'Plumbing'),
            ('electrical', 'Electrical'),
            ('ac', 'Air Conditioning'),
            ('furniture', 'Furniture'),
            ('other', 'Other'),
        ],
        string='Maintenance Type',
        default='all',
    )

    include_reservations = fields.Boolean(
        string='Include Reservation History',
        default=True,
    )

    include_tasks = fields.Boolean(
        string='Include Maintenance & Housekeeping History',
        default=True,
    )

    # =====================================================
    # Excel File
    # =====================================================

    excel_file = fields.Binary(
        string='Excel File',
        readonly=True,
    )

    excel_filename = fields.Char(
        string='Filename',
        readonly=True,
    )

    # =====================================================
    # Generate Excel Report
    # =====================================================

    def action_generate_report(self):
        self.ensure_one()

        if not self.room_id:
            raise UserError(_('Please select a room.'))

        room = self.room_id

        # Validate date range
        if (
            self.date_from
            and self.date_to
            and self.date_from > self.date_to
        ):
            raise UserError(
                _('Date From cannot be later than Date To.')
            )

        # At least one section must be selected
        if (
            not self.include_reservations
            and not self.include_tasks
        ):
            raise UserError(
                _('Please select at least one report section.')
            )

        # =================================================
        # Get Reservations
        # =================================================

        reservation_domain = [
            ('room_id', '=', room.id),
            ('state', '=', 'checked_out'),
            ('check_out', '!=', False),
        ]

        if self.date_from:
            reservation_domain.append(
                ('check_out', '>=', self.date_from)
            )

        if self.date_to:
            reservation_domain.append(
                ('check_out', '<=', self.date_to)
            )

        reservations = self.env['hotel.reservation'].search(
            reservation_domain,
            order='check_out desc, id desc',
        )

        # =================================================
        # Get Maintenance & Housekeeping Tasks
        # =================================================

        task_domain = [
            ('room_id', '=', room.id),
        ]

        if self.date_from:
            task_domain.append(
                ('scheduled_date', '>=', self.date_from)
            )

        if self.date_to:
            task_domain.append(
                ('scheduled_date', '<=', self.date_to)
            )

        # Filter by task type
        if self.task_type and self.task_type != 'all':
            task_domain.append(
                ('task_type', '=', self.task_type)
            )

        # Maintenance Type applies only to maintenance tasks.
        # If Housekeeping is selected, ignore maintenance type.
        if (
            self.maintenance_type
            and self.maintenance_type != 'all'
            and self.task_type != 'housekeeping'
        ):
            task_domain.append(
                ('task_type', '=', 'maintenance')
            )
            task_domain.append(
                ('maintenance_type', '=', self.maintenance_type)
            )

        tasks = self.env['hotel.housekeeping.task'].search(
            task_domain,
            order='scheduled_date desc, id desc',
        )

        # =================================================
        # Create Excel Workbook
        # =================================================

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True},
        )

        worksheet = workbook.add_worksheet('Room History')

        # =================================================
        # Excel Formats
        # =================================================

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'font_color': '#1F1F1F',
            'bg_color': '#EAF2F8',
            'align': 'left',
            'valign': 'vcenter',
            'indent': 1,
        })

        section_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'font_color': '#FFFFFF',
            'bg_color': '#4472C4',
            'align': 'left',
            'valign': 'vcenter',
            'indent': 1,
        })

        info_label_format = workbook.add_format({
            'bold': True,
            'font_color': '#404040',
            'bg_color': '#D9EAF7',
            'border': 1,
            'border_color': '#D9D9D9',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        info_value_format = workbook.add_format({
            'font_color': '#262626',
            'border': 1,
            'border_color': '#D9D9D9',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        reservation_header_format = workbook.add_format({
            'bold': True,
            'font_color': '#FFFFFF',
            'bg_color': '#5B9BD5',
            'border': 1,
            'border_color': '#FFFFFF',
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        maintenance_header_format = workbook.add_format({
            'bold': True,
            'font_color': '#FFFFFF',
            'bg_color': '#70AD47',
            'border': 1,
            'border_color': '#FFFFFF',
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        data_format = workbook.add_format({
            'border': 1,
            'border_color': '#D9D9D9',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        alternate_data_format = workbook.add_format({
            'border': 1,
            'border_color': '#D9D9D9',
            'bg_color': '#F2F7FC',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        date_format = workbook.add_format({
            'border': 1,
            'border_color': '#D9D9D9',
            'num_format': 'dd-mmm-yyyy',
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        alternate_date_format = workbook.add_format({
            'border': 1,
            'border_color': '#D9D9D9',
            'bg_color': '#F2F7FC',
            'num_format': 'dd-mmm-yyyy',
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        datetime_format = workbook.add_format({
            'border': 1,
            'border_color': '#D9D9D9',
            'num_format': 'dd-mmm-yyyy hh:mm',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        alternate_datetime_format = workbook.add_format({
            'border': 1,
            'border_color': '#D9D9D9',
            'bg_color': '#F2F7FC',
            'num_format': 'dd-mmm-yyyy hh:mm',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        currency_format = workbook.add_format({
            'border': 1,
            'border_color': '#D9D9D9',
            'num_format': '#,##0.00',
            'valign': 'vcenter',
            'align': 'right',
        })

        alternate_currency_format = workbook.add_format({
            'border': 1,
            'border_color': '#D9D9D9',
            'bg_color': '#F2F7FC',
            'num_format': '#,##0.00',
            'valign': 'vcenter',
            'align': 'right',
        })

        note_format = workbook.add_format({
            'italic': True,
            'font_color': '#666666',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        # =================================================
        # Helper: Write Date / Datetime
        # =================================================

        def write_date(row, col, value, alternate=False):
            normal_format = (
                alternate_data_format
                if alternate
                else data_format
            )

            if not value:
                worksheet.write_blank(
                    row,
                    col,
                    None,
                    normal_format,
                )
                return

            if isinstance(value, datetime):
                fmt = (
                    alternate_datetime_format
                    if alternate
                    else datetime_format
                )

                worksheet.write_datetime(
                    row,
                    col,
                    value,
                    fmt,
                )

            elif isinstance(value, date):
                value_datetime = datetime.combine(
                    value,
                    time.min,
                )

                fmt = (
                    alternate_date_format
                    if alternate
                    else date_format
                )

                worksheet.write_datetime(
                    row,
                    col,
                    value_datetime,
                    fmt,
                )

            else:
                worksheet.write(
                    row,
                    col,
                    str(value),
                    normal_format,
                )

        # =================================================
        # Helper: Write General Values
        # =================================================

        def write_value(row, col, value, alternate=False):
            fmt = (
                alternate_data_format
                if alternate
                else data_format
            )

            if value is None or value is False:
                worksheet.write_blank(
                    row,
                    col,
                    None,
                    fmt,
                )

            elif (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            ):
                worksheet.write_number(
                    row,
                    col,
                    value,
                    fmt,
                )

            else:
                worksheet.write(
                    row,
                    col,
                    str(value),
                    fmt,
                )

        # =================================================
        # Report Title
        # =================================================

        worksheet.merge_range(
            'A1:L1',
            'HOTEL - ROOM HISTORY REPORT',
            title_format,
        )

        worksheet.set_row(0, 30)

        # =================================================
        # Room Information
        # =================================================

        room_type_label = dict(
            room._fields['room_type'].selection
        ).get(
            room.room_type,
            room.room_type or '',
        )

        report_date = fields.Date.context_today(self)

        worksheet.write(
            'A3',
            'Room Number',
            info_label_format,
        )

        worksheet.write(
            'B3',
            room.room_number or '',
            info_value_format,
        )

        worksheet.write(
            'D3',
            'Room Type',
            info_label_format,
        )

        worksheet.write(
            'E3',
            room_type_label,
            info_value_format,
        )

        worksheet.write(
            'G3',
            'Floor',
            info_label_format,
        )

        worksheet.write(
            'H3',
            'Not configured',
            info_value_format,
        )

        worksheet.write(
            'J3',
            'Report Date',
            info_label_format,
        )

        worksheet.write_datetime(
            'K3',
            datetime.combine(report_date, time.min),
            date_format,
        )

        worksheet.set_row(2, 25)

        # Start report content at Excel row 6 (zero-based row 5)
        row = 5

        # =================================================
        # SECTION 1: RESERVATION HISTORY
        # =================================================

        if self.include_reservations:

            row = 5

            reservation_headers = [
                'Reservation Reference',
                'Guest',
                'Room Type',
                'Check-in',
                'Check-out',
                'Adults',
                'Children',
                'Nights',
                'Nightly Rate',
                'Room Total',
                'Total Amount',
                'Status',
            ]

            worksheet.merge_range(
                row,
                0,
                row,
                len(reservation_headers) - 1,
                '1. RESERVATION HISTORY',
                section_format,
            )

            worksheet.set_row(row, 25)
            row += 1

            for col, header in enumerate(reservation_headers):
                worksheet.write(
                    row,
                    col,
                    header,
                    reservation_header_format,
                )

            worksheet.set_row(row, 42)

            reservation_header_row = row
            row += 1

            reservation_state_labels = dict(
                self.env['hotel.reservation']
                ._fields['state'].selection
            )

            for index, reservation in enumerate(reservations):
                alternate = index % 2 == 1

                values = [
                    reservation.name or '',
                    reservation.guest_id.display_name or '',
                    room_type_label,
                    reservation.check_in,
                    reservation.check_out,
                    reservation.adults,
                    reservation.children,
                    reservation.nights,
                    reservation.nightly_rate,
                    reservation.room_total,
                    reservation.total_amount,
                    reservation_state_labels.get(
                        reservation.state,
                        reservation.state or '',
                    ),
                ]

                for col, value in enumerate(values):

                    if col in (3, 4):
                        write_date(
                            row,
                            col,
                            value,
                            alternate,
                        )

                    elif col in (8, 9, 10):
                        fmt = (
                            alternate_currency_format
                            if alternate
                            else currency_format
                        )

                        worksheet.write_number(
                            row,
                            col,
                            value or 0.0,
                            fmt,
                        )

                    else:
                        write_value(
                            row,
                            col,
                            value,
                            alternate,
                        )

                worksheet.set_row(row, 32)
                row += 1

            if not reservations:
                worksheet.merge_range(
                    row,
                    0,
                    row,
                    len(reservation_headers) - 1,
                    'No reservations found for this room.',
                    note_format,
                )

                worksheet.set_row(row, 25)
                row += 1

            reservation_last_row = row - 1

        # =================================================
        # SECTION 2: MAINTENANCE & HOUSEKEEPING HISTORY
        # =================================================

        if self.include_tasks:

            if self.include_reservations:
                row += 2

            maintenance_headers = [
                'Task Name',
                'Task Type',
                'Maintenance Type',
                'Assigned Staff',
                'Scheduled Date',
                'Start Date',
                'Done Date',
                'Status',
                'Description',
            ]

            worksheet.merge_range(
                row,
                0,
                row,
                len(maintenance_headers) - 1,
                (
                    '2. MAINTENANCE & HOUSEKEEPING HISTORY'
                    if self.include_reservations
                    else '1. MAINTENANCE & HOUSEKEEPING HISTORY'
                ),
                section_format,
            )

            worksheet.set_row(row, 25)
            row += 1

            for col, header in enumerate(maintenance_headers):
                worksheet.write(
                    row,
                    col,
                    header,
                    maintenance_header_format,
                )

            worksheet.set_row(row, 42)

            maintenance_header_row = row
            row += 1

            task_model = self.env['hotel.housekeeping.task']

            task_type_labels = dict(
                task_model._fields['task_type'].selection
            )

            maintenance_type_labels = dict(
                task_model._fields['maintenance_type'].selection
            )

            task_state_labels = dict(
                task_model._fields['state'].selection
            )

            for index, task in enumerate(tasks):
                alternate = index % 2 == 1

                values = [
                    task.name or '',
                    task_type_labels.get(
                        task.task_type,
                        task.task_type or '',
                    ),
                    maintenance_type_labels.get(
                        task.maintenance_type,
                        task.maintenance_type or '',
                    ),
                    task.assigned_user_id.display_name or '',
                    task.scheduled_date,
                    task.start_date,
                    task.done_date,
                    task_state_labels.get(
                        task.state,
                        task.state or '',
                    ),
                    task.description or '',
                ]

                for col, value in enumerate(values):

                    if col in (4, 5, 6):
                        write_date(
                            row,
                            col,
                            value,
                            alternate,
                        )

                    else:
                        write_value(
                            row,
                            col,
                            value,
                            alternate,
                        )

                worksheet.set_row(row, 42)
                row += 1

            if not tasks:
                worksheet.merge_range(
                    row,
                    0,
                    row,
                    len(maintenance_headers) - 1,
                    (
                        'No maintenance or housekeeping tasks '
                        'found for this room.'
                    ),
                    note_format,
                )

                worksheet.set_row(row, 25)
                row += 1

            maintenance_last_row = row - 1

        # =================================================
        # Column Widths
        # =================================================

        column_widths = {
            0: 25,   # Reservation Reference / Task Name
            1: 25,   # Guest / Task Type
            2: 23,   # Room Type / Maintenance Type
            3: 23,   # Check-in / Assigned Staff
            4: 19,   # Check-out / Scheduled Date
            5: 19,   # Adults / Start Date
            6: 19,   # Children / Done Date
            7: 17,   # Nights / Status
            8: 25,   # Nightly Rate / Description
            9: 17,   # Room Total
            10: 17,  # Total Amount
            11: 17,  # Reservation Status
        }

        for col, width in column_widths.items():
            worksheet.set_column(col, col, width)

        # =================================================
        # Autofilter
        # =================================================

        if self.include_reservations and reservations:
            worksheet.autofilter(
                reservation_header_row,
                0,
                reservation_last_row,
                len(reservation_headers) - 1,
            )

        # =================================================
        # Display Settings
        # =================================================

        if self.include_reservations:
            freeze_row = reservation_header_row + 1
        else:
            freeze_row = 6

        worksheet.freeze_panes(freeze_row, 0)

        worksheet.hide_gridlines(0)

        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 0)

        worksheet.set_margins(
            0.30,
            0.30,
            0.50,
            0.50,
        )

        worksheet.set_footer(
            '&CHotel | Room History Report'
        )

        # =================================================
        # Finish Workbook
        # =================================================

        workbook.close()

        output.seek(0)

        file_content = base64.b64encode(
            output.getvalue()
        )

        output.close()

        # =================================================
        # Filename
        # =================================================

        filename = 'Room_History_%s.xlsx' % (
            room.room_number or room.id
        )

        # =================================================
        # Save Excel File
        # =================================================

        self.write({
            'excel_file': file_content,
            'excel_filename': filename,
        })

        # =================================================
        # Download Excel File
        # =================================================

        return {
            'type': 'ir.actions.act_url',
            'url': (
                '/web/content/'
                '?model=room.history.report.wizard'
                '&id=%s'
                '&field=excel_file'
                '&filename_field=excel_filename'
                '&download=true'
            ) % self.id,
            'target': 'self',
        }
    def action_print_pdf(self):
        self.ensure_one()

        return self.env.ref(
            'hotel_management.action_report_room_history_pdf'
        ).report_action(self)