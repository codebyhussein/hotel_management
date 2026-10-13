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
            ('room_service', 'Room Service'),
        ],
        string='Task Type',
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

        # =================================================
        # Validate Date Range
        # =================================================

        if (
            self.date_from
            and self.date_to
            and self.date_from > self.date_to
        ):
            raise UserError(
                _('Date From cannot be later than Date To.')
            )

        # =================================================
        # Validate Report Sections
        # =================================================

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
        # Get Maintenance, Housekeeping & Room Service Tasks
        # =================================================

        task_domain = [
            ('room_id', '=', room.id),
        ]

        if self.date_from:
            task_domain.append(
                ('request_date', '>=', self.date_from)
            )

        if self.date_to:
            task_domain.append(
                ('request_date', '<=', self.date_to)
            )

        # Filter by task type.
        if self.task_type and self.task_type != 'all':
            task_domain.append(
                ('task_type', '=', self.task_type)
            )

        tasks = self.env['hotel.housekeeping.task'].search(
            task_domain,
            order='request_date desc, id desc',
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

        task_header_format = workbook.add_format({
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

        room_number_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'font_color': '#1F1F1F',
            'bg_color': '#E2F0D9',
            'border': 1,
            'border_color': '#D9D9D9',
            'align': 'center',
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
        # Helper: Get Selection Label
        # =================================================

        def get_selection_label(model, field_name, value):
            field = model._fields.get(field_name)

            if not field or not value:
                return ''

            selection = field.selection

            if callable(selection):
                selection = selection(model)

            return dict(selection or []).get(value, value)

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

        room_type_label = get_selection_label(
            room,
            'room_type',
            room.room_type,
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
            str(room.floor_number) if hasattr(room, 'floor_number') else 'Not configured',
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

        row = 5
        reservation_header_row = None
        reservation_last_row = None

        # =================================================
        # SECTION 1: RESERVATION HISTORY
        # =================================================

        if self.include_reservations:

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

            reservation_model = self.env['hotel.reservation']

            for index, reservation in enumerate(reservations):
                alternate = index % 2 == 1

                reservation_room_type = get_selection_label(
                    reservation_model,
                    'room_type',
                    reservation.room_type,
                )

                reservation_state = get_selection_label(
                    reservation_model,
                    'state',
                    reservation.state,
                )

                values = [
                    reservation.name or '',
                    reservation.guest_id.display_name or '',
                    reservation_room_type or room_type_label,
                    reservation.check_in,
                    reservation.check_out,
                    reservation.adults,
                    reservation.children,
                    reservation.nights,
                    reservation.nightly_rate,
                    reservation.room_total,
                    reservation.total_amount,
                    reservation_state,
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
        # SECTION 2: TASK HISTORY
        # =================================================

        if self.include_tasks:

            if self.include_reservations:
                row += 2

            task_headers = [
                'Room Number',
                'Task Reference',
                'Task Type',
                'Service Details',
                'Guest',
                'Assigned Staff',
                'Request Date',
                'Start Date',
                'Done Date',
                'Status',
                'Description',
            ]

            worksheet.merge_range(
                row,
                0,
                row,
                len(task_headers) - 1,
                (
                    '2. MAINTENANCE & HOUSEKEEPING HISTORY'
                    if self.include_reservations
                    else '1. MAINTENANCE & HOUSEKEEPING HISTORY'
                ),
                section_format,
            )

            worksheet.set_row(row, 25)
            row += 1

            for col, header in enumerate(task_headers):
                worksheet.write(
                    row,
                    col,
                    header,
                    task_header_format,
                )

            worksheet.set_row(row, 42)

            task_header_row = row
            row += 1

            task_model = self.env['hotel.housekeeping.task']

            task_type_labels = dict(
                task_model._fields['task_type'].selection
            )

            task_state_labels = dict(
                task_model._fields['state'].selection
            )

            room_tasks_start_row = row

            for index, task in enumerate(tasks):
                alternate = index % 2 == 1

                service_details = []

                if task.is_housekeeping:
                    housekeeping_label = get_selection_label(
                        task_model,
                        'housekeeping_type',
                        task.housekeeping_type,
                    )
                    service_details.append(
                        'Housekeeping: %s' % housekeeping_label
                    )

                if task.is_food_ordering:
                    food_items = task.food_item_ids

                    if food_items:
                        food_description = ', '.join(
                            '%s x %s' % (
                                line.name,
                                line.qty,
                            )
                            for line in food_items
                        )
                    else:
                        food_description = 'Food Ordering'

                    service_details.append(food_description)

                if task.is_laundry:
                    laundry_label = get_selection_label(
                        task_model,
                        'laundry_type',
                        task.laundry_type,
                    )
                    service_details.append(
                        'Laundry: %s' % laundry_label
                    )

                if task.is_extra_towels:
                    towels_label = get_selection_label(
                        task_model,
                        'extra_towels_type',
                        task.extra_towels_type,
                    )
                    service_details.append(
                        'Towels: %s' % towels_label
                    )

                if task.is_guest_supplies:
                    supplies_label = get_selection_label(
                        task_model,
                        'guest_supplies_type',
                        task.guest_supplies_type,
                    )
                    service_details.append(
                        'Guest Supplies: %s' % supplies_label
                    )

                if not service_details:
                    service_details.append(
                        task.description or '-'
                    )

                task_type_label = task_type_labels.get(
                    task.task_type,
                    task.task_type or '',
                )

                task_state_label = task_state_labels.get(
                    task.state,
                    task.state or '',
                )

                values = [
                    task.name or '',
                    task_type_label,
                    '; '.join(service_details),
                    task.guest_id.display_name or '',
                    task.assigned_user_id.display_name or '',
                    task.request_date,
                    task.start_date,
                    task.done_date,
                    task_state_label,
                    task.description or '',
                ]

                for value_index, value in enumerate(values):
                    col = value_index + 1

                    if col in (6, 7, 8):
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

            room_tasks_end_row = row - 1

            if tasks:
                if room_tasks_start_row == room_tasks_end_row:
                    worksheet.write(
                        room_tasks_start_row,
                        0,
                        room.room_number or '',
                        room_number_format,
                    )
                else:
                    worksheet.merge_range(
                        room_tasks_start_row,
                        0,
                        room_tasks_end_row,
                        0,
                        room.room_number or '',
                        room_number_format,
                    )

            else:
                worksheet.merge_range(
                    row,
                    0,
                    row,
                    len(task_headers) - 1,
                    (
                        'No maintenance, housekeeping, or room '
                        'service tasks found for this room.'
                    ),
                    note_format,
                )

                worksheet.set_row(row, 25)
                row += 1

        # =================================================
        # Column Widths
        # =================================================

        column_widths = {
            0: 16,
            1: 25,
            2: 20,
            3: 32,
            4: 22,
            5: 23,
            6: 20,
            7: 20,
            8: 20,
            9: 18,
            10: 35,
        }

        for col, width in column_widths.items():
            worksheet.set_column(col, col, width)

        # =================================================
        # Autofilter
        # =================================================

        if (
            self.include_reservations
            and reservations
            and reservation_header_row is not None
            and reservation_last_row is not None
            and reservation_last_row > reservation_header_row
        ):
            worksheet.autofilter(
                reservation_header_row,
                0,
                reservation_last_row,
                11,
            )

        # =================================================
        # Display Settings
        # =================================================

        if (
            self.include_reservations
            and reservation_header_row is not None
        ):
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

    # =====================================================
    # Print PDF
    # =====================================================

    def action_print_pdf(self):
        self.ensure_one()

        return self.env.ref(
            'hotel_management.action_report_room_history_pdf'
        ).report_action(self)