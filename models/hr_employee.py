# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class Employee(models.Model):
    _inherit = 'hr.employee'

    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo')
    variable_ids = fields.One2many('hu_productividad.empleado_variable', 'empleado_id')


class EmpleadoVariable(models.Model):
    _name = 'hu_productividad.empleado_variable'

    empleado_id = fields.Many2one('hr.employee', string='Empleado')
    variable_id = fields.Many2one('hu_productividad.variable', string='Variable')
    # tipo = fields.Char(related='variable_id.tipo')
    # valor = fields.Float(related='variable_id.valor')
