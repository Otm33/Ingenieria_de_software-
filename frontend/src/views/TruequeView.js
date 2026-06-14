import { PropuestaRequest, ResponderPropuestaRequest, ValidarCodigoRequest } from '../models/RequestModels.js';
import { GeneralView } from './GeneralView.js';

export class TruequeView extends GeneralView {
    constructor(apiClient) {
        super(apiClient);
    }

    async crearPropuesta(formData) {
        const req = new PropuestaRequest(formData);
        req.validar();
        const res = await this.apiClient.post('/api/trueques/propuestas/crear/', req);
        return res.data;
    }

    async responderPropuesta(trueque_id, accion) {
        const req = new ResponderPropuestaRequest({ accion });
        req.validar();
        const res = await this.apiClient.post(`/api/trueques/${trueque_id}/responder/`, req);
        return res.data;
    }

    async finalizarTrueque(trueque_id) {
        const res = await this.apiClient.post(`/api/trueques/${trueque_id}/finalizar/`, {});
        return res.data;
    }

    async validarCodigo(trueque_id, codigo) {
        const req = new ValidarCodigoRequest({ codigo });
        req.validar();
        const res = await this.apiClient.post(`/api/trueques/${trueque_id}/validar-codigo/`, req);
        return res.data;
    }
}
