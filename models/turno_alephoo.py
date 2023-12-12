# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import mysql.connector


class Productividad(models.Model):
    _name = 'hu_productividad.turno_alephoo'
    _description = 'Productividad - Turno Alephoo'

    employee_id = fields.Many2one('hr.employee', string='Empleado')
    turno_id = fields.Integer(string='Turno ID')
    item_turno_id = fields.Integer(string='Item turno ID')
    mes = fields.Char(string='Mes')
    fecha = fields.Date(string='Fecha')
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
    hora = fields.Float(string='Hora')
    estado = fields.Char(string='Estado')
    especialidad = fields.Char(string='Especialidad')

    paciente_nombre = fields.Char(string='Nombre paciente')
    paciente_dni = fields.Char(string='DNI')
    paciente_fecha_nacimiento = fields.Date(string='Fecha de nacimiento')
    paciente_edad = fields.Char(string='Edad')
    paciente_numero_hc = fields.Integer(string='Nro. de historia clínica')

    medico_nombre = fields.Char(string='Médico')
    medico_id = fields.Integer(string='Id médico')

    prestacion_nombre = fields.Char(string='Prestación')
    prestacion_codigo = fields.Char(string='Código prestación')
    prestacion_cantidad = fields.Integer(string='Cantidad prestación')

    importe = fields.Float(string='Importe')
    importe_coseguro = fields.Float(string='Importe coseguro')
    importe_total = fields.Float(string='Importe total')
    factura_nro = fields.Integer(string='Nro. Factura')

    computado_en_productividad = fields.Boolean(string='Computado en productividad', default=False)
    agregado_manualmente = fields.Boolean(string='Agregado manualmente', default=False)

    def sincronizar_datos_alephoo(self, anio_facturacion, mes_facturacion, turno_fecha_desde, turno_fecha_hasta, medico_id):
        query = """
SELECT 
  tp.id AS TURNOID, 
  (CASE WHEN MONTH(tp.fecha) = 1 THEN 'Enero' WHEN MONTH(tp.fecha) = 2 THEN 'Febrero' WHEN MONTH(tp.fecha) = 3 THEN 'Marzo' WHEN MONTH(tp.fecha) = 4 THEN 'Abril' WHEN MONTH(tp.fecha) = 5 THEN 'Mayo' WHEN MONTH(tp.fecha) = 6 THEN 'Junio' WHEN MONTH(tp.fecha) = 7 THEN 'Julio' WHEN MONTH(tp.fecha) = 8 THEN 'Agosto' WHEN MONTH(tp.fecha) = 9 THEN 'Septienbre' WHEN MONTH(tp.fecha) = 10 THEN 'Octubre' WHEN MONTH(tp.fecha) = 11 THEN 'Noviembre' WHEN MONTH(tp.fecha) = 12 THEN 'Diciembre' END) AS MES, 
  CONCAT(p.apellidos, ' ', p.nombres) AS PACIENTE, 
  p.documento AS DNI, 
  p.fecha_nacimiento AS FECHA_NACIMIENTO, 
  FORMAT(((DATEDIFF(NOW(), p.fecha_nacimiento)) / 365),0) AS EDAD, 
  dep.nombre AS SERVICIO, 
  es.nombre AS ESPECIALIDAD, 
  tp.fecha AS FECHA, 
  tp.hora AS HORA, 
  p.nro_hc AS NRO_HC, 
  dep.nombre AS DEPARTAMENTO, 
  es.nombre AS ESPECIALIDAD, 
  IF (ISNULL(con.evento_id),CONCAT(p2.apellidos, ' ', p2.nombres),CONCAT(medc.apellidos, ' ', medc.nombres)) AS MEDICO,
  pr.id AS MEDICO_ID,
  (CASE WHEN tp.estado_turno_id = 1 THEN 'PENDIENTE' WHEN tp.estado_turno_id = 2 THEN 'EN CURSO' WHEN tp.estado_turno_id = 3 THEN 'CANCELADO' WHEN tp.estado_turno_id = 4 THEN 'NO ASISTIO' WHEN tp.estado_turno_id = 5 THEN 'REALIZADO' WHEN tp.estado_turno_id = 6 THEN 'ARRIBO' WHEN tp.estado_turno_id = 7 THEN 'BLOQUEADO' WHEN tp.estado_turno_id = 8 THEN 'NO ATENDIDO' WHEN tp.estado_turno_id = 9 THEN 'VISTO' END) AS ESTADO_TURNO, 
  pl.nombre AS COBERTURA, 
  bo.numero AS NUMERO, 
  ia.numeroAutorizacion AS NUMERO_AUTORIZACION, 
  pre.nombre AS PRESTACION, 
  (CASE WHEN (SUBSTR(pre.codigo, 4, 2) = '42' AND SUBSTR(pre.codigo, 4, 8) <> '42.33.01') OR SUBSTR(pre.codigo, 4, 2) = '19' OR SUBSTR(pre.codigo, 4, 2) = '25' OR SUBSTR(pre.codigo, 4, 8) = '32.01.22' THEN 'Consulta' ELSE 'Practica' END) AS DETALLE, 
  pre.codigo AS CODIGO, 
  bi.cantidad AS CANTIDAD ,
  bi.monto / 100 AS PRECIO,
  IF(ISNULL(f.monto),0,f.monto / 100) as COPAGO,
  (bi.monto / 100 + IF(ISNULL(f.monto),0,f.monto / 100))* bi.cantidad AS TOTAL,
  (CASE WHEN bo.estado = 1 THEN 'ESTADO_NOCONFIRMADO' WHEN bo.estado = 2 THEN 'ESTADO_CONFIRMADO' WHEN bo.estado = 4 THEN 'ESTADO_PREFACTURADO' WHEN bo.estado = 5 THEN 'ESTADO_ANULADO o ESTADO_NOCOBRABLE' WHEN bo.estado = 6 THEN 'ESTADO_ELIMINADO' WHEN bo.estado = 7 THEN 'ESTADO_FACTURADO' WHEN bo.estado = 8 THEN 'ESTADO_FACTURADO_CON_NOTA' END) AS ESTADO, 
  tb.nombre AS TIPO, 
  IF (ISNULL(usum.id),usuc.username,usuc.username) AS MODIFICADO_POR, 
  IF ((ISNULL(bo.modificado_en) OR bo.modificado_en = '0000-00-00 00:00:00'),bo.creado_en,bo.modificado_en) AS FECHA_MOD, 
  fac.numero AS FAC_NUM, 
  fac.numero_manual AS FAC_NUM_MANUAL, 
  IF (NOT ISNULL(recp.id),rec.numero,'') AS REC_NRO,
  bi.id AS BONOITEMID
FROM turno_programado AS tp
INNER JOIN persona AS p ON ( tp.persona_id = p.id )
INNER JOIN bono AS bo ON ( bo.turnoprogramado_id = tp.id )
INNER JOIN tipobono AS tb ON ( bo.tipobono_id = tb.id )
INNER JOIN item_bono AS bi ON ( bi.bono_id = bo.id )
LEFT JOIN item_bono AS bi2 ON ( bi2.id = bi.item_bono_related )
LEFT JOIN bono AS bo2 ON ( bo2.id = bi2.bono_id )
LEFT JOIN prefacturaitem AS p3 ON ( p3.bono_id = bo2.id )
LEFT JOIN factura_prefactura AS fp ON ( fp.prefactura_id = p3.prefactura_id )
LEFT JOIN factura AS f ON ( f.id = fp.factura_id )
LEFT JOIN itemAutorizacion ia on ia.itemBonoId = bi.id
INNER JOIN prestacion AS pre ON (bi.prestacion_id = pre.id)
INNER JOIN plan AS pl ON (bo.plan_id = pl.id)
INNER JOIN agenda AS ag ON (tp.agenda_id = ag.id)
INNER JOIN asignacion AS asig ON (ag.asignacion_id = asig.id)
INNER JOIN especialidad AS es ON (asig.especialidad_id = es.id)
INNER JOIN departamento AS dep ON (es.departamento_id = dep.id)
INNER JOIN personal AS pr ON (asig.personal_id = pr.id)
INNER JOIN persona AS p2 ON (pr.persona_id = p2.id)
LEFT JOIN prefacturaitem AS prefi ON prefi.bono_id = bo.id
LEFT JOIN prefactura AS pref ON pref.id = prefi.prefactura_id
LEFT JOIN factura_prefactura AS fac_pre ON fac_pre.prefactura_id = pref.id
LEFT JOIN factura AS fac ON fac.id = fac_pre.factura_id
INNER JOIN documentofacturacion df ON df.id = fac.id 
INNER JOIN centrodecosto AS cc ON cc.id = fac.centrodecosto_id
LEFT JOIN recibo_factura AS reci_fac ON reci_fac.factura_id = fac.id
LEFT JOIN recibo AS rec ON rec.id = reci_fac.recibo_id
LEFT JOIN recibopago AS recp ON recp.recibo_id = rec.id 
LEFT JOIN consulta AS con ON con.id = tp.consulta_id
LEFT JOIN personal AS perc ON perc.id = con.personal_id
LEFT JOIN persona AS medc ON medc.id = perc.persona_id 
LEFT JOIN usuario AS usuc ON usuc.id = bo.creadopor_id
LEFT JOIN usuario AS usum ON usum.id = bo.modificadopor_id
LEFT JOIN persona_plan AS pp ON (pp.plan_id = bo.plan_id AND pp.persona_id = bo.persona_id)
WHERE IF (tb.id=10,
(SELECT COUNT(bo4.id) 
  FROM bono AS bo4 
  INNER JOIN item_bono AS bi4 ON ( bi4.bono_id = bo4.id )
  INNER JOIN prestacion AS pre4 on ( bi4.prestacion_id = pre4.id )
  INNER JOIN cotizacion AS coti4 ON ( coti4.prestacion_id = pre4.id )
  WHERE (bo4.tipobono_id = 1 or bo4.tipobono_id = 2) AND bo4.turnoprogramado_id = bo.turnoprogramado_id AND bo4.estado <> 6 
  ) ,0)  = 0 
AND 
IF ((tb.id=1 OR tb.id=2) AND bo.estado<>7 ,
(SELECT COUNT(bo5.id) 
  FROM bono AS bo5 
  INNER JOIN item_bono AS bi5 ON ( bi5.bono_id = bo5.id )
  INNER JOIN prestacion AS pre5 on ( bi5.prestacion_id = pre5.id )
  INNER JOIN cotizacion AS coti5 ON ( coti5.prestacion_id = pre5.id )
  WHERE bo5.tipobono_id = 10 AND bo5.turnoprogramado_id = bo.turnoprogramado_id 
  AND bo5.estado = 8 AND bo5.plan_id = pl.id  )     
,0) = 0 
AND 
IF ((tb.id=1 OR tb.id=2) AND (bo.estado=5 OR bo.estado=6 ) ,
(SELECT COUNT(bo6.id) 
  FROM bono AS bo6 
  INNER JOIN item_bono AS bi6 ON ( bi6.bono_id = bo6.id )
  INNER JOIN prestacion AS pre6 on ( bi6.prestacion_id = pre6.id )
  INNER JOIN cotizacion AS coti6 ON ( coti6.prestacion_id = pre6.id )
  WHERE bo6.tipobono_id = 10 AND bo6.turnoprogramado_id = bo.turnoprogramado_id )     
,0) = 0 AND
 (cc.id = 10 OR cc.id = 8) 
 AND YEAR(df.fecha) = {anio}
 AND MONTH(df.fecha) = {mes}
 AND IF(ISNULL(con.evento_id),pr.id = {medico_id},con.personal_id = {medico_id}) 
 AND bo.estado = 7 
GROUP BY 
  bo.id, bi.id 
UNION DISTINCT  
SELECT 
  tp.id AS TURNOID, 
  (CASE WHEN MONTH(tp.fecha) = 1 THEN 'Enero' WHEN MONTH(tp.fecha) = 2 THEN 'Febrero' WHEN MONTH(tp.fecha) = 3 THEN 'Marzo' WHEN MONTH(tp.fecha) = 4 THEN 'Abril' WHEN MONTH(tp.fecha) = 5 THEN 'Mayo' WHEN MONTH(tp.fecha) = 6 THEN 'Junio' WHEN MONTH(tp.fecha) = 7 THEN 'Julio' WHEN MONTH(tp.fecha) = 8 THEN 'Agosto' WHEN MONTH(tp.fecha) = 9 THEN 'Septienbre' WHEN MONTH(tp.fecha) = 10 THEN 'Octubre' WHEN MONTH(tp.fecha) = 11 THEN 'Noviembre' WHEN MONTH(tp.fecha) = 12 THEN 'Diciembre' END) AS MES, 
  CONCAT(p.apellidos, ' ', p.nombres) AS PACIENTE, 
  p.documento AS DNI, 
  p.fecha_nacimiento AS FECHA_NACIMIENTO, 
  FORMAT(((DATEDIFF(NOW(), p.fecha_nacimiento)) / 365),0) AS EDAD, 
  dep.nombre AS SERVICIO, 
  es.nombre AS ESPECIALIDAD, 
  tp.fecha AS FECHA, 
  tp.hora AS HORA, 
  p.nro_hc AS NRO_HC, 
  dep.nombre AS DEPARTAMENTO, 
  es.nombre AS ESPECIALIDAD, 
  IF (ISNULL(con.evento_id),CONCAT(p2.apellidos, ' ', p2.nombres),CONCAT(medc.apellidos, ' ', medc.nombres)) AS MEDICO,
  pr.id AS MEDICO_ID,
  (CASE WHEN tp.estado_turno_id = 1 THEN 'PENDIENTE' WHEN tp.estado_turno_id = 2 THEN 'EN CURSO' WHEN tp.estado_turno_id = 3 THEN 'CANCELADO' WHEN tp.estado_turno_id = 4 THEN 'NO ASISTIO' WHEN tp.estado_turno_id = 5 THEN 'REALIZADO' WHEN tp.estado_turno_id = 6 THEN 'ARRIBO' WHEN tp.estado_turno_id = 7 THEN 'BLOQUEADO' WHEN tp.estado_turno_id = 8 THEN 'NO ATENDIDO' WHEN tp.estado_turno_id = 9 THEN 'VISTO' END) AS ESTADO_TURNO, 
  pl.nombre AS COBERTURA, 
  bo.numero AS NUMERO, 
  ia.numeroAutorizacion AS NUMERO_AUTORIZACION, 
  pre.nombre AS PRESTACION, 
  (CASE WHEN (SUBSTR(pre.codigo, 4, 2) = '42' AND SUBSTR(pre.codigo, 4, 8) <> '42.33.01') 
    OR SUBSTR(pre.codigo, 4, 2) = '19' 
    OR SUBSTR(pre.codigo, 4, 2) = '25' 
    OR SUBSTR(pre.codigo, 4, 8) = '32.01.22' THEN 'Consulta' ELSE 'Practica' END
  ) AS DETALLE, 
  pre.codigo AS CODIGO, 
  bi.cantidad AS CANTIDAD ,
  bi.monto / 100 AS PRECIO ,
  IF(ISNULL(f.monto),0,f.monto / 100) as COPAGO,
  (bi.monto / 100 + IF(ISNULL(f.monto),0,f.monto / 100))* bi.cantidad AS TOTAL ,
  (CASE WHEN bo.estado = 1 THEN 'ESTADO_NOCONFIRMADO' WHEN bo.estado = 2 THEN 'ESTADO_CONFIRMADO' WHEN bo.estado = 4 THEN 'ESTADO_PREFACTURADO' WHEN bo.estado = 5 THEN 'ESTADO_ANULADO o ESTADO_NOCOBRABLE' WHEN bo.estado = 6 THEN 'ESTADO_ELIMINADO' WHEN bo.estado = 7 THEN 'ESTADO_FACTURADO' WHEN bo.estado = 8 THEN 'ESTADO_FACTURADO_CON_NOTA' END) AS ESTADO, 
  tb.nombre AS TIPO, 
  IF (ISNULL(usum.id),usuc.username,usuc.username) AS MODIFICADO_POR, 
  IF ((ISNULL(bo.modificado_en) OR bo.modificado_en = '0000-00-00 00:00:00'),bo.creado_en,bo.modificado_en) AS FECHA_MOD, 
  fac.numero AS FAC_NUM, 
  fac.numero_manual AS FAC_NUM_MANUAL, 
  IF (NOT ISNULL(recp.id),rec.numero,'') AS REC_NRO,
  bi.id AS BONOITEMID
FROM turno_programado AS tp
INNER JOIN persona AS p ON ( tp.persona_id = p.id )
INNER JOIN bono AS bo ON (bo.turnoprogramado_id = tp.id)
INNER JOIN tipobono AS tb ON ( bo.tipobono_id = tb.id )
INNER JOIN item_bono AS bi ON ( bi.bono_id = bo.id )
LEFT JOIN item_bono AS bi2 ON ( bi2.id = bi.item_bono_related )
LEFT JOIN bono AS bo2 ON ( bo2.id = bi2.bono_id )
LEFT JOIN prefacturaitem AS p3 ON ( p3.bono_id = bo2.id )
LEFT JOIN factura_prefactura AS fp ON ( fp.prefactura_id = p3.prefactura_id )
LEFT JOIN factura AS f ON ( f.id = fp.factura_id )
LEFT JOIN itemAutorizacion ia on ia.itemBonoId = bi.id
INNER JOIN prestacion AS pre ON (bi.prestacion_id = pre.id)
INNER JOIN plan AS pl ON (bo.plan_id = pl.id)
INNER JOIN agenda AS ag ON 	(tp.agenda_id = ag.id)
INNER JOIN asignacion AS asig ON (ag.asignacion_id = asig.id)
INNER JOIN especialidad AS es ON (asig.especialidad_id = es.id)
INNER JOIN departamento AS dep ON (es.departamento_id = dep.id)
INNER JOIN personal AS pr ON (asig.personal_id = pr.id)
INNER JOIN persona AS p2 ON (pr.persona_id = p2.id)
LEFT JOIN prefacturaitem AS prefi ON prefi.bono_id = bo.id
LEFT JOIN prefactura AS pref ON pref.id = prefi.prefactura_id
LEFT JOIN factura_prefactura AS fac_pre ON fac_pre.prefactura_id = pref.id
LEFT JOIN factura AS fac ON fac.id = fac_pre.factura_id
INNER JOIN documentofacturacion df ON df.id = fac.id 
INNER JOIN centrodecosto AS cc ON cc.id = fac.centrodecosto_id
LEFT JOIN recibo_factura AS reci_fac ON reci_fac.factura_id = fac.id
LEFT JOIN recibo AS rec ON rec.id = reci_fac.recibo_id
LEFT JOIN recibopago AS recp ON recp.recibo_id = rec.id 
LEFT JOIN consulta AS con ON con.id = tp.consulta_id
LEFT JOIN personal AS perc ON perc.id = con.personal_id
LEFT JOIN persona AS medc ON medc.id = perc.persona_id 
LEFT JOIN usuario AS usuc ON usuc.id = bo.creadopor_id
LEFT JOIN usuario AS usum ON usum.id = bo.modificadopor_id
LEFT JOIN persona_plan AS pp ON (pp.plan_id = bo.plan_id AND pp.persona_id = bo.persona_id)
WHERE IF (tb.id=10,
(SELECT COUNT(bo4.id) 
  FROM bono AS bo4 
  INNER JOIN item_bono AS bi4 ON ( bi4.bono_id = bo4.id )
  INNER JOIN prestacion AS pre4 on ( bi4.prestacion_id = pre4.id )
  INNER JOIN cotizacion AS coti4 ON ( coti4.prestacion_id = pre4.id )
  WHERE (bo4.tipobono_id = 1 or bo4.tipobono_id = 2) AND bo4.turnoprogramado_id = bo.turnoprogramado_id AND bo4.estado <> 6 
  ) ,0)  = 0 
AND 
IF ((tb.id=1 OR tb.id=2) AND bo.estado<>7 ,
(SELECT COUNT(bo5.id) 
  FROM bono AS bo5 
  INNER JOIN item_bono AS bi5 ON ( bi5.bono_id = bo5.id )
  INNER JOIN prestacion AS pre5 on ( bi5.prestacion_id = pre5.id )
  INNER JOIN cotizacion AS coti5 ON ( coti5.prestacion_id = pre5.id )
  WHERE bo5.tipobono_id = 10 AND bo5.turnoprogramado_id = bo.turnoprogramado_id 
  AND bo5.estado = 8 AND bo5.plan_id = pl.id  )     
,0) = 0 
AND 
IF ((tb.id=1 OR tb.id=2) AND (bo.estado=5 OR bo.estado=6 ) ,
(SELECT COUNT(bo6.id) 
  FROM bono AS bo6 
  INNER JOIN item_bono AS bi6 ON ( bi6.bono_id = bo6.id )
  INNER JOIN prestacion AS pre6 on ( bi6.prestacion_id = pre6.id )
  INNER JOIN cotizacion AS coti6 ON ( coti6.prestacion_id = pre6.id )
  WHERE bo6.tipobono_id = 10 AND bo6.turnoprogramado_id = bo.turnoprogramado_id )     
,0) = 0 AND 
  tp.fecha BETWEEN '{fecha_desde}' AND '{fecha_hasta}' 
  AND (cc.id = 11) 
  AND IF(ISNULL(con.evento_id),pr.id = {medico_id},con.personal_id = {medico_id}) 
  AND bo.estado = 7 
GROUP BY 
  bo.id, bi.id 
ORDER BY PACIENTE ASC;
        """.format(anio=anio_facturacion, mes=mes_facturacion, medico_id=medico_id, fecha_desde=turno_fecha_desde, fecha_hasta=turno_fecha_hasta)

        host = self.env["ir.config_parameter"].get_param("hu.turnos_alephoo_host", False)
        port = self.env["ir.config_parameter"].get_param("hu.turnos_alephoo_port", False)
        user = self.env["ir.config_parameter"].get_param("hu.turnos_alephoo_user", False)
        password = self.env["ir.config_parameter"].get_param("hu.turnos_alephoo_password", False)
        database = self.env["ir.config_parameter"].get_param("hu.turnos_alephoo_database", False)

        if not all([host, port, user, password, database]):
            raise ValidationError('Los datos de conexión a la base de datos no están configurados.')

        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        for result in results:
            turno_existente = self.search([
                ('item_turno_id', '=', result[33]),
                ('prestacion_codigo', '=', result[21]),
            ])
            if not turno_existente:
                empleado_id = self.env['hr.employee'].search([('id_alephoo', '=', result[14])], limit=1).id or None
                self.create({
                    'employee_id': empleado_id,
                    'turno_id': result[0],
                    'item_turno_id': result[33],
                    'mes': result[1],
                    'paciente_nombre': result[2],
                    'paciente_dni': result[3],
                    'paciente_fecha_nacimiento': result[4],
                    'paciente_edad': result[5],
                    'fecha': result[8],
                    'dia': str(result[8].weekday()),
                    'hora': result[9].total_seconds() / 3600,
                    'especialidad': result[7],
                    'paciente_numero_hc': result[10],
                    'medico_nombre': result[13],
                    'medico_id': result[14],
                    'estado': result[15],
                    'prestacion_nombre': result[19],
                    'prestacion_codigo': result[21],
                    'prestacion_cantidad': result[22],
                    'importe': result[23],
                    'importe_coseguro': result[24],
                    'importe_total': result[25],
                    'factura_nro': result[30]
                })
