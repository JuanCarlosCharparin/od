# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class Employee(models.Model):
    _inherit = 'hr.employee'

    id_alephoo = fields.Integer(string='ID Alephoo')
    fecha_ultimo_calculo_productividad = fields.Datetime(string='Fecha de último cálculo de productividad')
    metodo_calculo_employee_ids = fields.One2many('hu_productividad.metodo_calculo_employee', 'employee_id', string='Métodos de cálculo')

    def calcular_productividad(self, mes, anio):
        primer_dia_mes_actual = datetime(anio, mes, 1)
        primer_dia_mes_anterior = primer_dia_mes_actual - relativedelta(months=1)
        ultimo_dia_mes_anterior = (primer_dia_mes_actual - timedelta(days=1)).replace(hour=23, minute=59)
        self.env['hu_productividad.turno_alephoo'].sincronizar_datos_alephoo(anio, mes, primer_dia_mes_anterior, ultimo_dia_mes_anterior, self.id_alephoo)
        calculos_productividad = []
        for metodo_calculo_employee in self.metodo_calculo_employee_ids:
            if metodo_calculo_employee.metodo_calculo_id.active:
                for metodo_calculo_variable in metodo_calculo_employee.metodo_calculo_id.metodo_calculo_variable_ids:
                    #Por cada variable, buscar los turnos que tenga el médico con esas practicas. Además, en caso de que en la prestación, el campo es_receta esté en True,
                    #se debe buscar por especialidad 'RECETAS MEDICAS' ya que el turno puede venir con otro código de prestación pero la especialidad indica que es receta
                    codigo_prestaciones = []
                    buscar_por_especialidad_recetas_medicas = False
                    for prestacion in metodo_calculo_variable.prestacion_ids:
                        codigo_prestaciones.append(prestacion.codigo)
                        if prestacion.es_receta:
                            buscar_por_especialidad_recetas_medicas = True
                    #Toma también las prestaciones de los agrupadores
                    for agrupador_prestacion in metodo_calculo_variable.agrupador_prestaciones_ids:
                        for prestacion in agrupador_prestacion.prestacion_ids:
                            codigo_prestaciones.append(prestacion.codigo)
                            if prestacion.es_receta:
                                buscar_por_especialidad_recetas_medicas = True

                    filtros_turnos = [
                        ('employee_id', '=', self.id),
                        ('computado_en_productividad', '=', False),
                        ('prestacion_codigo', 'in', codigo_prestaciones)
                    ]

                    if buscar_por_especialidad_recetas_medicas:
                        filtros_turnos.append(('espcialidad', '=', 'RECETAS MEDICAS'))

                    #En caso de corresponder agrega los filtros por día y horario
                    if metodo_calculo_employee.horario_especifico:
                        filtros_turnos.append(('dia', '=', metodo_calculo_employee.dia))
                        filtros_turnos.append(('hora', '>=', metodo_calculo_employee.hora_desde))
                        filtros_turnos.append(('hora', '<=', metodo_calculo_employee.hora_hasta))

                    turnos_alephoo = self.env['hu_productividad.turno_alephoo'].search(filtros_turnos)

                    importe = 0
                    if turnos_alephoo:
                        turnos_alephoo.write({'computado_en_productividad': True})

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
                        'turno_alephoo_ids': turnos_alephoo.ids,
                        'importe': importe,
                        'cantidad_practicas_realizadas': len(turnos_alephoo),
                        'metodo_calculo_id': metodo_calculo_employee.metodo_calculo_id.id,
                        'horario': metodo_calculo_employee.get_nombre_horario(),
                        'metodo_calculo_variable_id': metodo_calculo_variable.id,
                        'forma_calculo': metodo_calculo_variable.forma_calculo,
                        'base': metodo_calculo_variable.base,
                        'tipo_punto_id': metodo_calculo_variable.tipo_punto_id.id,
                        'valor_punto': metodo_calculo_variable.valor_punto,
                        'porcentaje': metodo_calculo_variable.porcentaje,
                        'valor_monto_fijo': metodo_calculo_variable.valor_monto_fijo
                    })

        return calculos_productividad


    def get_empleados_a_calcular_productividad(self, mes, anio, limite=False):
        mes_actual = datetime.now().year
        anio_actual = datetime.now().month
        if mes == mes_actual and anio == anio_actual:
            return self._get_empleados_a_calcular_productividad_mes_actual(limite)
        else:
            return self._get_empleados_a_calcular_productividad_segun_mes(mes, anio, limite=False)


    def _get_empleados_a_calcular_productividad_mes_actual(self, limite):
        fecha_actual = datetime.now()
        primer_dia_mes_actual = datetime(fecha_actual.year, fecha_actual.month, 1)
        primer_dia_mes_actual = primer_dia_mes_actual.replace(hour=0, minute=0, second=0, microsecond=0)

        return self.search([
            ('metodo_calculo_employee_ids', '!=', False),
            ('fecha_ultimo_calculo_productividad', '<=', primer_dia_mes_actual)
        ], limit=limite)

    def _get_empleados_a_calcular_productividad_segun_mes(self, mes, anio, limite):
        empleados_ya_calculados = []
        productividad = self.env['hu_productividad.productividad'].buscar_o_crear_productividad(mes, anio)
        for productividad_empleado in productividad.productividad_empleado_ids:
            empleados_ya_calculados.append(productividad_empleado.employee_id.id)

        return self.search([
            ('id', 'not in', empleados_ya_calculados),
            ('metodo_calculo_employee_ids', '!=', False)
        ], limit=limite)
