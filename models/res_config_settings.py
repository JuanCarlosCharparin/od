# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    productividad_proxima_fecha_calculo = fields.Date('Próxima fecha de cálculo de productividad')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            productividad_proxima_fecha_calculo=self.env["ir.config_parameter"].get_param("productividad_proxima_fecha_calculo", False),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param("productividad_proxima_fecha_calculo", self.productividad_proxima_fecha_calculo or False)
