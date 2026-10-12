{
    'name': "Hotel Management",

    'summary': "Complete hotel management solution for managing rooms, guests, bookings, and daily hotel operations.",

    'description': """
Hotel Management
================

A complete Odoo solution for managing hotel operations efficiently.

Key Features:
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

    'category': 'Uncategorized',
    'version': '0.1',

    'application': True,
    'installable': True,

    'depends': [
        'base',
        'mail',
        'website',
        'crm',
    ],

    'data': [
        # Security
        'security/hotel_security.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',

        # Data
        'data/hotel_reservation_data.xml',
        'data/inquiry_confirmation.xml',

        # Views
        'views/guest.xml',
        'views/room_service.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_room.xml',
        'views/property.xml',
        'views/res_user.xml',

        'views/crm_lead_view.xml',
        # wizards
        'views/maintenance_request.xml',
        'views/mail_template.xml',
        'wizard/room_report_excel.xml',
        # Website Templates
        'views/homepage.xml',
        'views/room_templates_website.xml',
        'views/online_booking_templates.xml',

        # Menus
        'wizard/room_report_excel.xml',
        'wizard/room_report_piecharm.xml',

    
         
        'views/guest.xml',
        'views/hotel_reservation_views.xml',
        'views/room_report.xml',
        'views/menus.xml',
        'wizard/room_service.xml',
        
    ],

    'demo': [
        'demo/demo.xml',
    ],
}
