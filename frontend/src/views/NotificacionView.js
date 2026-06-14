import { GeneralView } from './GeneralView.js';

export class NotificacionView extends GeneralView {
    constructor(apiClient) {
        super(apiClient);
    }

    async listarNotificaciones(incluir_leidas = false) {
        const res = await this.apiClient.get(`/api/notificaciones/?incluir_leidas=${incluir_leidas}`);
        return res.data;
    }

    async marcarLeida(notificacion_id) {
        const res = await this.apiClient.post('/api/notificaciones/marcar-leida/', { notificacion_id });
        return res.data;
    }
}
