import { PropuestaMultipleRequest, ValidarCodigoParRequest } from '../models/RequestModels.js';
import { GeneralView } from './GeneralView.js';

export class TruequeMultipleView extends GeneralView {
    constructor(apiClient) {
        super(apiClient);
    }

    async crearPropuestaMultiple(formData) {
        const req = new PropuestaMultipleRequest(formData);
        req.validar();
        const res = await this.apiClient.post('/api/trueques-multiples/', req);
        return res.data;
    }

    async aceptarPropuesta(trueque_multiple_id) {
        const res = await this.apiClient.post(`/api/trueques-multiples/${trueque_multiple_id}/aceptar/`, {});
        return res.data;
    }

    async rechazarPropuesta(trueque_multiple_id) {
        const res = await this.apiClient.post(`/api/trueques-multiples/${trueque_multiple_id}/rechazar/`, {});
        return res.data;
    }

    async validarCodigoPar(trueque_multiple_id, par, codigo) {
        const req = new ValidarCodigoParRequest({ codigo, par });
        req.validar();
        const res = await this.apiClient.post(`/api/trueques-multiples/${trueque_multiple_id}/validar-codigo/`, req);
        return res.data;
    }

    async finalizarPar(trueque_multiple_id, par) {
        const res = await this.apiClient.post(`/api/trueques-multiples/${trueque_multiple_id}/finalizar-par/`, { par });
        return res.data;
    }
}
