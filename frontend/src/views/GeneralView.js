export class GeneralView {
    constructor(apiClient) {
        this.apiClient = apiClient; // Dependencia inyectada para hacer requests HTTP
    }

    /**
     * Muestra errores de validación o del servidor en la UI.
     * Podría interactuar con el DOM o el framework frontend (Vue/React).
     */
    mostrarError(mensaje) {
        console.error("Error UI:", mensaje);
        // Implementación específica de la interfaz de usuario
    }

    /**
     * Muestra mensajes de éxito.
     */
    mostrarExito(mensaje) {
        console.log("Éxito UI:", mensaje);
        // Implementación específica de la interfaz de usuario
    }
}
