# -*- coding: utf-8 -*-
{
    'name': "hotel_management",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'summary': "Complete hotel management solution for managing rooms, guests, bookings, and daily hotel operations.",
    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    'depends': ['base', 'mail','website'],


    # always loaded
    'data': [
        'security/hotel_security.xml',  # 👈 لازم يتحمل الأول عشان يتعرفوا الـ Groups! (تأكدي من اسم الملف عندك)
        'security/ir.model.access.csv',  # 👈 ملف الـ CSV ييجي بعده
        'views/views.xml',
        'views/templates.xml',
        'views/housekeeping.xml',
        'views/guest.xml',

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


        'views/housekeeping.xml',
        'views/guest.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_room.xml',
        'views/property.xml',
        'views/res_user.xml',
        'views/menus.xml',
        #  website templates
        'views/homepage.xml',
        'views/room_templates_website.xml',
        'views/online_booking_templates.xml',
        'views/menus.xml',
    ],

    # only loaded in demonstration mode

    'demo': [
        'demo/demo.xml',
    ],
}

