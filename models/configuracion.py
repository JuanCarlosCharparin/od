# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductividadVariable(models.Model):
    _name = 'hu_productividad.variable'

    name = fields.Char(string='Nombre', required=True)
    tipo = fields.Char(string='Tipo', required=True)
    valor = fields.Float(string='Valor')


class ProductividadMetodoCalculo(models.Model):
    _name = 'hu_productividad.metodo_calculo'

    name = fields.Char(string='Nombre', required=True)
    empleado_ids = fields.One2many('hu_productividad.empleado', 'metodo_calculo_id')
