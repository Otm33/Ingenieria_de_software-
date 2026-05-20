// src/types/comunidad.ts

export interface ConfiguracionComunidad {
  horas_iniciales_base: number;
  permitir_excedentes: boolean;
  vigencia_credito_comercial: number;
}

export type EstadoMiembro = 'ACTIVO' | 'SUSPENDIDO' | 'PENDIENTE' | 'INACTIVO';

export interface MiembroComunidad {
  id?: number;
  usuario_id?: number;
  cedula: string;
  nombre: string;
  correo: string;
  telefono?: string;
  estado: EstadoMiembro;
  es_administrador: boolean;
  id_comercio_vinculado?: number | null;
}

export interface CuentaSaldo {
  id?: number;
  miembro_id: number;
  saldo_horas: number;
  estado_cuenta: string;
}

export interface AuthVerificarResponse {
  // Ajusta esto según lo que devuelva tu VerificarAutorizacionSerializer
  autorizado: boolean;
  miembro?: MiembroComunidad;
  token?: string; 
}
