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

    # always loaded
    'data': [
        
    #   security files
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'security/groups.xml',
        
        # data files

        'data/hotel_reservation_data.xml',
        
        # Views files
        'views/hotel_room.xml',
        'views/property.xml',
        'views/res_user.xml',
        'wizard/room_report_excel.xml',

    
        'views/housekeeping.xml',
        'views/guest.xml',
                'views/hotel_reservation_views.xml',
        'views/menus.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],
}
