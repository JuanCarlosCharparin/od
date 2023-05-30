# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class ProductividadPrestacion(models.Model):
    _name = 'hu_productividad.prestacion'
    _description = 'Productividad - Prestación'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    active = fields.Boolean(string='Activo', default=True)


class ProductividadTipoPunto(models.Model):
    _name = 'hu_productividad.tipo_punto'
    _description = 'Productividad - Tipo de punto'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Descripción', required=True)
    valor = fields.Float(string='Valor $', required=True, tracking=True)
    active = fields.Boolean(string='Activo', default=True)
