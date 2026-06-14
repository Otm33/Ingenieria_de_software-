import { CrearPublicacionRequest, ActualizarPublicacionRequest } from '../models/RequestModels.js';
import { GeneralView } from './GeneralView.js';

export class PublicacionView extends GeneralView {
    constructor(apiClient) {
        super(apiClient);
    }

    async crearPublicacion(formData) {
        try {
            const requestModel = new CrearPublicacionRequest(formData);
            requestModel.validar();

            const response = await this.apiClient.post('/api/publicaciones/', requestModel);
            this.mostrarExito("Publicación creada correctamente.");
            return response.data;
        } catch (error) {
            this.mostrarError(error.message || "Error al crear la publicación.");
            throw error;
        }
    }

    async actualizarEstado(id, esta_activa) {
        try {
            const requestModel = new ActualizarPublicacionRequest({ esta_activa });
            requestModel.validar();

            const response = await this.apiClient.put(`/api/publicaciones/${id}/`, requestModel);
            this.mostrarExito("Estado actualizado.");
            return response.data;
        } catch (error) {
            this.mostrarError(error.message || "Error al actualizar estado.");
            throw error;
        }
    }

    async obtenerCartelera(filtros = {}) {
        try {
            const params = new URLSearchParams(filtros).toString();
            const url = params ? `/api/cartelera/?${params}` : '/api/cartelera/';
            const response = await this.apiClient.get(url);
            return response.data;
        } catch (error) {
            this.mostrarError("Error al cargar la cartelera.");
            throw error;
        }
    }

    async listarMisPublicaciones() {
        try {
            const response = await this.apiClient.get('/api/mis-publicaciones/');
            return response.data;
        } catch (error) {
            this.mostrarError("Error al cargar tus publicaciones.");
            throw error;
        }
    }
}
