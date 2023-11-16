# -*- coding: utf-8 -*-
{
    'name': "Hospital Universitario - Productividad",

    'summary': 'Módulo de inventario para Hospital Universitario',

    'author': "Hexium Software Factory",
    'website': "https://hexium.com.ar",
    'category': 'Uncategorized',
    'version': '1.0',
    'installable': True,
    'application': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],
    "external_dependencies": {"python": ["mysql"]},

    # always loaded
    'data': [
        # Views
        'views/productividad_views.xml',
        'views/metodo_calculo_views.xml',
        'views/configuracion_views.xml',
        'views/hr_employee.xml',

        # Menu
        'views/menu.xml',

        # Data
        'data/ir.module.category.csv',
        'data/email_template/envio_productividad_medico.xml',
        'data/crons.xml',

        # Security
        'security/res.groups.xml',
        'security/ir.rules.xml',
        'security/ir.model.access.csv',
    ],
}