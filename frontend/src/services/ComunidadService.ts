// src/services/ComunidadService.ts
import type { AuthVerificarResponse } from '../types/comunidad';

// Como estás usando Docker, tu backend responde en el puerto 8000
const API_BASE_URL = 'http://localhost:8000/api/comunidad';

export class ComunidadService {
  
  /**
   * Envía el archivo CSV al backend de Django
   */
  static async importarMiembros(archivoCSV: File): Promise<any> {
  const formData = new FormData();
  formData.append('archivo', archivoCSV); 

  const response = await fetch(`${API_BASE_URL}/miembros/importar/`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    // 💡 AQUÍ EL CAMBIO: Leemos el JSON de error que mandó Django
    const datosError = await response.json().catch(() => null);
    
    // Extraemos el mensaje específico (ej: "Faltan columnas", "Usuario ya existe", etc.)
    const mensajeEspecifico = datosError?.error || datosError?.detail || JSON.stringify(datosError) || response.statusText;
    
    throw new Error(mensajeEspecifico);
  }

  return await response.json();
}

  /**
   * Verifica el correo electrónico
   */
  static async verificarAutorizacion(correo: string): Promise<AuthVerificarResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/verificar/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ correo }),
    });

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('Usuario no autorizado.');
      }
      throw new Error(`Error en el servidor: ${response.statusText}`);
    }

    return await response.json();
  }
}
