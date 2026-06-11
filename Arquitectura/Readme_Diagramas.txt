#   Visualización de Diagramas del Proyecto (PlantUML)

Para la documentación de la arquitectura, casos de uso y flujos de este proyecto, se han utilizado diagramas de código abierto mediante **PlantUML** (archivos con extensión `.puml`).

Siga los pasos a continuación para poder visualizarlos correctamente dentro de **Visual Studio Code**.



##  Prerrequisitos del Sistema

El motor de PlantUML requiere que su sistema operativo cuente con los siguientes componentes instalados y configurados en las variables de entorno (`PATH`):

1. **Java (JRE o JDK):** Necesario para ejecutar el renderizador.
2. **Graphviz:** Requerido por PlantUML para generar la distribución visual de los diagramas complejos.



##  Configuración en Visual Studio Code

1. Diríjase a la sección de **Extensiones** (`Ctrl + Shift + X` o `Cmd + Shift + X` en macOS).
2. Busque e instale la extensión llamada **PlantUML** (desarrollada por *jebbs*).



##  Cómo Visualizar los Diagramas

1. Abra cualquier archivo del repositorio que tenga la extensión `.puml`.
2. Para activar la vista previa interactiva, utilice el siguiente atajo de teclado según su sistema:
   * **Windows / Linux:** `Alt + D`
   * **macOS:** `Option + D`
3. Se abrirá un panel lateral dinámico en VS Code que renderizará el diagrama y se actualizará automáticamente ante cualquier cambio en el archivo de texto.



##  Alternativa sin Instalación

Si prefiere evaluar los diagramas sin configurar el entorno local en VS Code, puede abrir cualquier archivo `.puml` con un editor de texto común, copiar todo su contenido y pegarlo directamente en el servidor web oficial:

[PlantUML Live Viewer](https://www.plantuml.com/plantuml/)