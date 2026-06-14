import { GeneralView } from './GeneralView.js';

export class MatchmakingView extends GeneralView {
    constructor(apiClient) {
        super(apiClient);
    }

    async obtenerMatches(publicacionId = null) {
        try {
            const url = publicacionId
                ? `/api/matchmaking/?publicacion_id=${publicacionId}`
                : '/api/matchmaking/';
            const response = await this.apiClient.get(url);
            return response.data;
        } catch (error) {
            this.mostrarError("Error al cargar coincidencias.");
            throw error;
        }
    }

    async verificarCoincidencia(publicacionId) {
        try {
            if (!publicacionId) throw new Error("ID de publicación requerido.");
            const response = await this.apiClient.get(`/api/matchmaking/?publicacion_id=${publicacionId}&accion=verificar_coincidencia`);
            return response.data;
        } catch (error) {
            this.mostrarError(error.message || "Error al verificar coincidencia.");
            throw error;
        }
    }
}
