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

    def calcular_productividad(self, mes, anio):
        #@TODO valores hardcodeados
        turno_fecha_desde = '2023-02-01'
        turno_fecha_hasta = '2023-02-28'
        anio_facturacion = 2023
        mes_facturacion = 3
        self.env['hu_productividad.turno_alephoo'].sincronizar_datos_alephoo(anio_facturacion, mes_facturacion, turno_fecha_desde, turno_fecha_hasta, self.id_alephoo)
        calculos_productividad = []
        for metodo_calculo in self.metodo_calculo_ids:
            for metodo_calculo_variable in metodo_calculo.metodo_calculo_variable_ids:
                #Por cada variable, buscar los turnos que tenga el médico con esas practicas
                codigo_prestaciones = []
                for prestacion in metodo_calculo_variable.prestacion_ids:
                    codigo_prestaciones.append(prestacion.codigo)
                turnos_alephoo = self.env['hu_productividad.turno_alephoo'].search([
                    ('employee_id', '=', self.id),
                    ('fecha', '>=', turno_fecha_desde),
                    ('fecha', '<=', turno_fecha_hasta),
                    ('computado_en_productividad', '=', False),
                    ('prestacion_codigo', 'in', codigo_prestaciones)
                ])

                importe = 0
                #Calculo por puntaje: (Cantidad prestac de alephoo - Base) * Valor del punto) * Tipo_punto.valor
                if metodo_calculo_variable.forma_calculo == 'puntaje':
                    importe = (len(turnos_alephoo) - metodo_calculo_variable.base) * metodo_calculo_variable.valor_punto * metodo_calculo_variable.tipo_punto_id.valor

                #Calculo por porcentaje_facturado: (sumatoria del total de lo facturado por esa prestación) * %
                elif metodo_calculo_variable.forma_calculo == 'porcentaje_facturado':
                    total_facturado = 0
                    for turno_alephoo in turnos_alephoo:
                        total_facturado += turno_alephoo.importe_total

                    importe = total_facturado * metodo_calculo_variable.porcentaje / 100

                #Calculo por monto_fijo_cantidad: cantidad de turnos de esa prestación * monto fijo
                elif metodo_calculo_variable.forma_calculo == 'monto_fijo_cantidad':
                    importe = len(turnos_alephoo) * metodo_calculo_variable.valor_monto_fijo

                #Calculo por monto_fijo
                elif metodo_calculo_variable.forma_calculo == 'monto_fijo':
                    importe = metodo_calculo_variable.valor_monto_fijo

                #Calculo por formula_vieja: ((Cantidad de prestac de alephoo  * valor del punto) - Base) * Tipo_punto.valor
                elif metodo_calculo_variable.forma_calculo == 'formula_vieja':
                    importe = ((len(turnos_alephoo) * metodo_calculo_variable.valor_punto) - metodo_calculo_variable.base) * metodo_calculo_variable.tipo_punto_id.valor



                calculos_productividad.append({
                    'importe': importe,
                    'cantidad_practicas_realizadas': len(turnos_alephoo),
                    'metodo_calculo_id': metodo_calculo.id,
                    'metodo_calculo_variable_id': metodo_calculo_variable.id,
                    'forma_calculo': metodo_calculo_variable.forma_calculo,
                    'base': metodo_calculo_variable.base,
                    'tipo_punto_id': metodo_calculo_variable.tipo_punto_id,
                    'valor_punto': metodo_calculo_variable.valor_punto,
                    'porcentaje': metodo_calculo_variable.porcentaje,
                    'valor_monto_fijo': metodo_calculo_variable.valor_monto_fijo
                })

        return calculos_productividad


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
