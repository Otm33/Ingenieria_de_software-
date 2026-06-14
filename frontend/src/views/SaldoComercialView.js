import { EmitirVueltoRequest, PagarConSaldoRequest } from '../models/RequestModels.js';
import { GeneralView } from './GeneralView.js';

export class SaldoComercialView extends GeneralView {
    constructor(apiClient) {
        super(apiClient);
    }

    async emitirVuelto(formData) {
        const req = new EmitirVueltoRequest(formData);
        req.validar();
        const res = await this.apiClient.post('/api/comercio/emitir-vuelto/', req);
        return res.data;
    }

    async pagarConSaldo(formData) {
        const req = new PagarConSaldoRequest(formData);
        req.validar();
        const res = await this.apiClient.post('/api/comercio/pagar/', req);
        return res.data;
    }

    async verSaldo() {
        const res = await this.apiClient.get('/api/mi-saldo-comercial/');
        return res.data;
    }
}
