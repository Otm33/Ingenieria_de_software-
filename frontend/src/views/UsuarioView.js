import { RegistroUsuarioRequest } from '../models/RequestModels.js';
import { GeneralView } from './GeneralView.js';

export class UsuarioView extends GeneralView {
    constructor(apiClient) {
        super(apiClient);
    }

    /**
     * Captura los datos de registro, crea el DTO, valida localmente y envía al backend.
     */
    async registrarUsuario(formData) {
        try {
            // 1. Crear el RequestModel (DTO)
            const requestModel = new RegistroUsuarioRequest(formData);

            // 2. Validación Dual (Frontend)
            requestModel.validar();

            // 3. Enviar petición al Router del Backend
            const response = await this.apiClient.post('/api/usuarios/registro/', requestModel);

            // 4. Manejar resultado
            this.mostrarExito(response.data.mensaje);
            return response.data;
        } catch (error) {
            // Manejar errores de validación local o del backend
            this.mostrarError(error.message || "Error al registrar el usuario.");
            throw error;
        }
    }
}
