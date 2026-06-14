import { ResenaRequest, ResenaMultipleRequest } from '../models/RequestModels.js';
import { GeneralView } from './GeneralView.js';

export class ResenaView extends GeneralView {
    constructor(apiClient) {
        super(apiClient);
    }

    async registrarResena(formData) {
        const req = new ResenaRequest(formData);
        req.validar();
        const res = await this.apiClient.post('/api/resenas/', req);
        return res.data;
    }

    async registrarResenaMultiple(formData) {
        const req = new ResenaMultipleRequest(formData);
        req.validar();
        const res = await this.apiClient.post('/api/resenas-multiples/', req);
        return res.data;
    }
}
