# Bookmark Directories - Plugin para Terminator

Un navegador de directorios controlado por teclado para [Terminator](https://gnome-terminator.org/). Guarda tus rutas favoritas, salta entre directorios al instante y navega tu historial - sin soltar el teclado.

![Python](https://img.shields.io/badge/python-3.6%2B-blue)
![GTK](https://img.shields.io/badge/GTK-3-green)
![Terminator](https://img.shields.io/badge/Terminator-plugin-orange)

> [🇬🇧 English](README.md) | 🇪🇸 Español

---

## Características

| Función | Descripción |
|---------|-------------|
|  **Marcadores** | Guarda directorios con un alias personalizado |
|  **Recientes** | Últimos 10 directorios visitados vía el plugin |
|  **Frecuentes** | Top 10 extraídos del historial de bash/zsh |
|  **Git repos** | Repositorios detectados automáticamente y resaltados |
|  **pushd / popd** | Stack de navegación en memoria - ve donde quieras y vuelve con un atajo |
|  **Vista previa** | Listado del directorio seleccionado, opcional |
|  **Búsqueda inteligente** | Prefix → substring → fuzzy, en ese orden de prioridad |
|  **Cambio de idioma** | Cambia toda la interfaz entre inglés y español desde la cabecera del popup |

---

## Atajos de teclado

| Atajo | Acción |
|-------|--------|
| `Ctrl+B` | Abrir el selector de directorios (modo cd) |
| `Ctrl+→` | Abrir el selector en modo pushd (guarda la posición actual) |
| `Ctrl+←` | Hacer popd y volver al directorio anterior sin abrir ningún popup |
| `Enter` | Confirmar el directorio seleccionado (cd o pushd según el modo) |
| Doble clic | Igual que Enter |

---

## Cambio de idioma

La cabecera del popup incluye dos botones de bandera: **🇬🇧** para inglés y **🇪🇸** para español. Al pulsar cualquiera de ellos, toda la interfaz se traduce al instante - etiquetas, tooltips, placeholders, cabeceras de sección y botones de diálogo. El idioma seleccionado se recuerda durante el resto de la sesión.

---

## pushd / popd

El plugin implementa un stack de navegación ligero, similar a los built-ins `pushd` y `popd` del shell:

- **`Ctrl+→` (pushd)** - Guarda el directorio actual en el stack y navega al que selecciones. El título del popup cambia a `→ pushd` para que siempre sepas en qué modo estás.
- **`Ctrl+←` (popd)** - Navega de vuelta al último directorio guardado y lo elimina del stack. Sin popup, sin ruido en la terminal.

El stack es **por sesión** (solo en memoria). Se reinicia al cerrar Terminator, lo que hace el comportamiento predecible.

```
Estás en:    ~/projects/web
Ctrl+→  →  seleccionas ~/projects/api       stack: [~/projects/web]
Ctrl+→  →  seleccionas /var/log             stack: [~/projects/web, ~/projects/api]
Ctrl+←                                      → vuelves a ~/projects/api
Ctrl+←                                      → vuelves a ~/projects/web
Ctrl+←                                      → stack vacío, no pasa nada
```

---

## Búsqueda inteligente

El buscador filtra todas las secciones a la vez con una estrategia de tres niveles:

1. **Prefix match** - `pro` encuentra `projects` (máxima prioridad)
2. **Substring** - `cts` encuentra `projects`
3. **Fuzzy** - `prjs` encuentra `projects` (todos los caracteres en orden)

El filtro se detiene en el primer nivel que produce resultados, así los hits de prefix siempre aparecen antes que los fuzzy.

---

## Secciones del popup

| Sección | Origen |
|---------|--------|
| ** Stack** | Directorios actualmente en el stack pushd |
| ** Marcadores** | Tus favoritos guardados con alias |
| ** Recientes** | Últimos 10 dirs navegados vía el plugin (sesión actual) |
| ** Frecuentes** | Top 10 de `~/.bash_history` / `~/.zsh_history` (comandos `cd`) |
| ** Git Repos** | Repos detectados en `~`, `~/projects`, `~/dev`, `~/code`, `~/workspace`, `~/repos`, `~/src` |

---

## Instalación

```bash
cp bookmark_directories.py ~/.config/terminator/plugins/
```

1. Abre Terminator
2. Ve a **Preferencias → Plugins**
3. Activa **BookmarkDirectoriesPlugin**
4. Reinicia Terminator

---

## Gestión de marcadores

- Botón ** Guardar aquí** (arriba a la derecha) - guarda el directorio actual con alias opcional. Incluye explorador gráfico de carpetas (`...`).
- Botón ** Eliminar** - borra el marcador seleccionado (solo activo en la sección Marcadores).
- Los marcadores se guardan en `~/.config/terminator/bm_bookmarks.json` y persisten entre sesiones.

---

## Vista previa

Al activarla, seleccionar cualquier entrada muestra el contenido del directorio en un panel inferior:

-  carpetas
-  enlaces simbólicos
-  archivos ejecutables

Toggle con el botón **👁** en la cabecera del popup. La preferencia persiste en `~/.config/terminator/bm_config.json`.

---

## Archivos de configuración

| Archivo | Contenido |
|---------|-----------|
| `~/.config/terminator/bm_bookmarks.json` | Marcadores guardados |
| `~/.config/terminator/bm_config.json` | Preferencias (`show_preview`) |

---

## Requisitos

- Python 3.6+
- Terminator con soporte de plugins
- GTK 3
- Sin dependencias externas
