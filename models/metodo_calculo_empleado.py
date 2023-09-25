# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class MetodoCalculoEmpleado(models.Model):
    _name = 'hu_productividad.metodo_calculo_employee'
    _description = 'Productividad - Método de calculo empleado'
    _order = 'horario_especifico desc, especialidad'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de calculo', required=True)
    especialidad = fields.Char(string='Especialidad', help='En caso de estar vacío se contemplarán todas las especialidades')
    horario_especifico = fields.Boolean(string='Horario específico', default=False)
    dia = fields.Selection(
        string='Día',
        selection=[
            ('0', 'Lunes'),
            ('1', 'Martes'),
            ('2', 'Miércoles'),
            ('3', 'Jueves'),
            ('4', 'Viernes'),
            ('5', 'Sábado'),
            ('6', 'Domingo')
        ]
    )
    hora_desde = fields.Float(string='Hora desde')
    hora_hasta = fields.Float(string='Hora hasta')

    def get_nombre_horario(self):
        nombre_horario = 'N/A'
        if self.horario_especifico:
            dia = dict(self._fields['dia'].selection).get(self.dia)
            hora_desde = str(timedelta(seconds=self.hora_desde * 3600))
            hora_hasta = str(timedelta(seconds=self.hora_hasta * 3600))
            nombre_horario = dia + ' - ' + hora_desde + ' a ' + hora_hasta + ' hs'

        return nombre_horario