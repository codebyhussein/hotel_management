# -*- coding: utf-8 -*-
{
    'name': "Hotel Management",

    'summary': "Complete hotel management solution for managing rooms, guests, bookings, and daily hotel operations.",

    'description': """
Hotel Management
================

A complete Odoo solution for managing hotel operations efficiently.

Key Features:\n
- Manage hotel rooms and room types.
- Manage guests and their information.
- Create and manage hotel bookings.
- Track room availability and booking status.
- Manage check-in and check-out operations.
- Organize hotel data through clear and user-friendly views.
- Support efficient day-to-day hotel management.

This module provides a centralized system to simplify hotel management
and improve operational efficiency.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'application': True,   # <-- ضيفيها
    'installable': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    
        'data': [
            'security/ir.model.access.csv',
            'data/hotel_reservation_data.xml',
            'views/views.xml',
            'views/templates.xml',
            'views/hotel_reservation_views.xml',
            'report/reservation_report.xml',
            'data/mail_template_data.xml',
            'data/hotel_reminder_data.xml',
            'wizard/hotel_reservation_report_wizard_views.xml',
            'wizard/hotel_room_change_wizard_views.xml',
            'wizard/hotel_group_booking_wizard_views.xml',
            'wizard/hotel_extend_stay_wizard_views.xml',
            'views/hotel_reservation_dashboard.xml',
        ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
