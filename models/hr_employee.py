# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime


class Employee(models.Model):
    _inherit = 'hr.employee'

    id_alephoo = fields.Integer(string='ID Alephoo')
    fecha_ultimo_calculo_productividad = fields.Datetime(string='Fecha de último cálculo de productividad')
    # metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo')
    metodo_calculo_ids = fields.Many2one(
        comodel_name='hu_productividad.metodo_calculo',
        relation='hu_productividad_employee_metodo_calculo',
        colum1='employee_id',
        colum2='metodo_calculo_id',
        string='Métodos de cálculo'
    )

    def calcular_productividad(self):
        #@TODO calcular la productividad del empleado y retornar un array con los detalles según cada método de calculo que tenga el empleado
        for metodo_calculo in self.metodo_calculo_ids:
            completar_codigo = 1

        return [{}, {}]


    def get_empleados_a_calcular_productividad(self, mes, anio, limite=False):
        mes_actual = datetime.now().year
        anio_actual = datetime.now().month
        if mes == mes_actual and anio == anio_actual:
            return self.get_empleados_a_calcular_productividad_mes_actual(limite)
        else:
            return self._get_empleados_a_calcular_productividad_segun_mes(mes, anio, limite=False)


    def _get_empleados_a_calcular_productividad_mes_actual(self, limite):
        fecha_actual = datetime.now()
        primer_dia_mes_actual = datetime(fecha_actual.year, fecha_actual.month, 1)
        primer_dia_mes_actual = primer_dia_mes_actual.replace(hour=0, minute=0, second=0, microsecond=0)

        return self.search([
            ('metodo_calculo_ids', '!=', False),
            ('fecha_ultimo_calculo_productividad', '<=', primer_dia_mes_actual)
        ], limite=limite)

    def _get_empleados_a_calcular_productividad_segun_mes(self, mes, anio, limite):
        empleados_ya_calculados = []
        productividad = self.env['hu_productividad.productividad'].buscar_o_crear_productividad(mes, anio)
        for productividad_empleado in productividad.productividad_empleado_ids:
            empleados_ya_calculados.append(productividad_empleado.employee_id.id)

        return self.search([
            ('id', 'not in', empleados_ya_calculados),
            ('metodo_calculo_ids', '!=', False)
        ], limite=limite)
