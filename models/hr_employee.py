# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class Employee(models.Model):
    _inherit = 'hr.employee'

    id_alephoo = fields.Integer(string='ID Alephoo')
    fecha_ultimo_calculo_productividad = fields.Datetime(string='Fecha de último cálculo de productividad')
    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo') #@TODO Permitir más de un método de calculo por empleado

    # variable_ids = fields.One2many('hu_productividad.empleado_variable', 'empleado_id') #@TODO esto es necesario?


# class EmpleadoVariable(models.Model):
#     _name = 'hu_productividad.empleado_variable'
#
#     empleado_id = fields.Many2one('hr.employee', string='Empleado')
#     variable_id = fields.Many2one('hu_productividad.prestacion', string='Prestación')
    # tipo = fields.Char(related='variable_id.tipo')
    # valor = fields.Float(related='variable_id.valor')
